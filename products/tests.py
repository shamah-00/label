from django.test import TestCase
from django.urls import reverse
from products.models import Order, Shipment


class CustomerOrderTrackingTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            customer_name="Shipping Test Customer",
            customer_email="shipping-test@example.com",
            customer_phone="5550100100",
            shipping_address="100 Test Street",
            shipping_city="Springfield",
            shipping_state="MA",
            shipping_postal_code="01109",
            shipping_country="United States",
        )
        self.shipment = Shipment.objects.create(
            order=self.order,
            carrier="UPS",
            shipping_method="Ground Saver",
            tracking_number="1ZTEST123",
            status="shipped",
            tracking_url="",
        )

    def test_customer_can_find_order_using_order_number_and_email(self):
        response = self.client.post(
            reverse("track_order"),
            {
                "order_number": str(self.order.pk),
                "email": self.order.customer_email,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["order"].pk, self.order.pk)
        self.assertEqual(
            response.context["tracking_url"],
            "https://www.ups.com/track?tracknum=1ZTEST123",
        )

    def test_wrong_email_does_not_reveal_order(self):
        response = self.client.post(
            reverse("track_order"),
            {
                "order_number": str(self.order.pk),
                "email": "wrong@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["order"])
        self.assertTrue(response.context["error_message"])

    def test_existing_https_tracking_url_is_preserved(self):
        self.shipment.tracking_url = "https://tracking.example.test/parcel/123"
        self.shipment.save(update_fields=["tracking_url"])
        response = self.client.post(
            reverse("track_order"),
            {
                "order_number": str(self.order.pk),
                "email": self.order.customer_email,
            },
        )
        self.assertEqual(
            response.context["tracking_url"],
            "https://tracking.example.test/parcel/123",
        )

from decimal import Decimal
from unittest.mock import Mock, patch

import requests
from django.test import TestCase
from django.urls import reverse

from products.models import Order, OrderItem, Product, Shipment


class CheckoutShippoWorkflowTests(TestCase):
    """Checkout integration tests use mocked Shippo responses only."""

    def setUp(self):
        self.product = Product.objects.create(
            name="Automated Shipping Test Product",
            slug="automated-shipping-test-product",
            price=Decimal("25.00"),
            stock=10,
            is_available=True,
            shipping_weight_lb=Decimal("2.00"),
            shipping_length_in=Decimal("12.00"),
            shipping_width_in=Decimal("8.00"),
            shipping_height_in=Decimal("2.00"),
        )

        session = self.client.session
        session["cart"] = {str(self.product.pk): 2}
        session.save()

        self.checkout_data = {
            "action": "ajax_get_rates",
            "payment_method": "check",
            "customer_name": "Checkout Test Customer",
            "customer_email": "checkout-test@example.com",
            "customer_phone": "5550100300",
            "shipping_address": "100 Test Street",
            "shipping_address2": "",
            "shipping_city": "Springfield",
            "shipping_state": "MA",
            "shipping_postal_code": "01109",
            "shipping_country": "United States",
            "notes": "Automated test only",
        }

        self.shippo_response = {
            "object_id": "shippo_shipment_test_only",
            "rates": [
                {
                    "object_id": "rate_test_only_123",
                    "provider": "UPS",
                    "servicelevel": {"name": "Ground Saver", "token": "ups_ground"},
                    "amount": "12.50",
                    "currency": "USD",
                    "estimated_days": 3,
                }
            ],
        }

    def mocked_shippo_response(self):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = self.shippo_response
        return response

    @patch.dict("os.environ", {"SHIPPO_API_TOKEN": "test_token_only"})
    @patch("requests.post")
    def test_checkout_creates_order_item_and_shipment(self, mock_post):
        mock_post.return_value = self.mocked_shippo_response()

        rates_response = self.client.post(
            reverse("checkout"), self.checkout_data
        )
        self.assertEqual(rates_response.status_code, 200)
        self.assertTrue(rates_response.json()["ok"])
        self.assertEqual(
            rates_response.json()["rates"][0]["object_id"],
            "rate_test_only_123",
        )
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["address_to"]["state"], "MA")
        self.assertEqual(payload["address_to"]["zip"], "01109")
        self.assertEqual(len(payload["parcels"]), 2)

        order_data = dict(self.checkout_data)
        order_data["action"] = "place_order"
        order_data["shipping_rate_id"] = "rate_test_only_123"

        order_response = self.client.post(reverse("checkout"), order_data)

        self.assertEqual(order_response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.customer_email, "checkout-test@example.com")
        self.assertEqual(order.subtotal, Decimal("50.00"))
        self.assertEqual(order.shipping_cost, Decimal("12.50"))
        self.assertEqual(order.total, Decimal("62.50"))

        item = OrderItem.objects.get(order=order)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal("25.00"))

        shipment = Shipment.objects.get(order=order)
        self.assertEqual(shipment.shippo_rate_id, "rate_test_only_123")
        self.assertEqual(shipment.carrier, "UPS")
        self.assertEqual(shipment.status, "pending")
        self.assertFalse(shipment.shippo_transaction_id)
        self.assertFalse(shipment.label_url)

        session = self.client.session
        self.assertEqual(session.get("cart"), {})
        self.assertNotIn("shippo_checkout_rates", session)

        # Only rates were requested. No real label transaction was made.
        self.assertEqual(mock_post.call_count, 1)
        self.assertIn(
            "https://api.goshippo.com/shipments/",
            mock_post.call_args.args[0],
        )

    @patch.dict("os.environ", {"SHIPPO_API_TOKEN": "test_token_only"})
    @patch("requests.post")
    def test_shippo_connection_failure_preserves_cart_and_creates_no_order(
        self, mock_post
    ):
        mock_post.side_effect = requests.Timeout("simulated test timeout")

        response = self.client.post(
            reverse("checkout"), self.checkout_data
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        self.assertTrue(response.json()["error"])

        session = self.client.session
        self.assertEqual(
            session["cart"], {str(self.product.pk): 2}
        )
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.assertEqual(Shipment.objects.count(), 0)
