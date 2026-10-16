import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from products.models import Order, Shipment


class StaffShippingDashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="shipping_test_boss",
            email="shipping-test-boss@example.com",
            password="test-only-password-123",
        )
        self.client.force_login(self.user)

        self.order = Order.objects.create(
            customer_name="Staff Shipping Test",
            customer_email="staff-shipping-test@example.com",
            customer_phone="5550100200",
            shipping_address="200 Test Street",
            shipping_city="Springfield",
            shipping_state="MA",
            shipping_postal_code="01109",
            shipping_country="United States",
        )
        self.shipment = Shipment.objects.create(
            order=self.order,
            carrier="UPS",
            shipping_method="Ground Saver",
            status="pending",
            shippo_rate_id="rate_test_only_123",
        )

    def test_staff_can_update_shipment_and_order_status(self):
        response = self.client.post(
            reverse("staff_shipping_dashboard"),
            {
                "action": "update",
                "shipment_id": str(self.shipment.pk),
                "status": "in_transit",
                "carrier": "UPS",
                "shipping_method": "Ground Saver",
                "estimated_delivery": "",
                "tracking_number": "1ZTEST456",
                "notes": "Automated regression test only",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.shipment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(self.shipment.status, "in_transit")
        self.assertEqual(self.shipment.tracking_number, "1ZTEST456")
        self.assertEqual(
            self.shipment.tracking_url,
            "https://www.ups.com/track?tracknum=1ZTEST456",
        )
        self.assertEqual(self.order.status, "shipped")

    @patch("requests.post")
    def test_label_purchase_is_blocked_when_safety_switch_is_off(
        self, mock_shippo_post
    ):
        previous = os.environ.get("THE_LABEL_GROUP_ALLOW_LIVE_SHIPPO_PURCHASES")
        try:
            os.environ["THE_LABEL_GROUP_ALLOW_LIVE_SHIPPO_PURCHASES"] = "false"

            response = self.client.post(
                reverse("staff_shipping_dashboard"),
                {
                    "action": "purchase_label",
                    "shipment_id": str(self.shipment.pk),
                    "shippo_rate_id": self.shipment.shippo_rate_id,
                },
            )

            self.assertEqual(response.status_code, 302)
            mock_shippo_post.assert_not_called()

            self.shipment.refresh_from_db()
            self.assertEqual(self.shipment.shippo_transaction_id, "")
            self.assertEqual(self.shipment.label_url, "")
        finally:
            if previous is None:
                os.environ.pop(
                    "THE_LABEL_GROUP_ALLOW_LIVE_SHIPPO_PURCHASES", None
                )
            else:
                os.environ[
                    "THE_LABEL_GROUP_ALLOW_LIVE_SHIPPO_PURCHASES"
                ] = previous
