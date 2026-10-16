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
