import logging
import os
import re
from decimal import Decimal

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)
API = "https://api.goshippo.com"
MARKER = re.compile(r"\[SHIPPO_ORDER_ID:([^\]]+)\]")


def get_token():
    for key in ("SHIPPO_API_TOKEN", "SHIPPO_API_KEY", "SHIPPO_TOKEN"):
        value = os.environ.get(key) or getattr(settings, key, None)
        if value:
            return str(value).strip()
    return ""


def money(value):
    return str(Decimal(value or 0).quantize(Decimal("0.01")))


def sync_order_to_shippo(order):
    try:
        match = MARKER.search(order.notes or "")
        if match:
            return True, "Already synced: " + match.group(1)

        token = get_token()
        if not token:
            return False, "Shippo API token is not configured."

        country = (order.shipping_country or "").strip().upper()
        if country not in (
            "US", "USA", "UNITED STATES",
            "UNITED STATES OF AMERICA"
        ):
            return False, "Only US shipping addresses are supported."

        required = (
            order.customer_name,
            order.shipping_address,
            order.shipping_city,
            order.shipping_state,
            order.shipping_postal_code,
        )
        if not all(required):
            return False, "Shipping address is incomplete."

        line_items = []

        for item in order.items.all():
            quantity = int(item.quantity or 1)
            total = item.total_price

            if total is None:
                total = Decimal(item.unit_price or 0) * quantity

            line_items.append({
                "title": str(
                    item.product_name or "THE LABEL GROUP product"
                ),
                "quantity": quantity,
                "total_price": money(total),
                "currency": "USD",
            })

        if not line_items:
            return False, "Order has no line items."

        shipment = getattr(order, "shipment", None)
        shipping_method = ""

        if shipment:
            shipping_method = (
                shipment.shipping_method or shipment.carrier or ""
            )

        order_number = "TLG-%06d" % order.pk

        payload = {
            "placed_at": (
                order.created_at or timezone.now()
            ).isoformat(),

            "to_address": {
                "name": order.customer_name,
                "street1": order.shipping_address,
                "city": order.shipping_city,
                "state": order.shipping_state,
                "zip": order.shipping_postal_code,
                "country": "US",
                "phone": order.customer_phone or "",
                "email": order.customer_email or "",
            },

            "from_address": {
                "name": "The Label Group LLC",
                "company": "The Label Group LLC",
                "street1": "580 St. James Avenue",
                "city": "Springfield",
                "state": "MA",
                "zip": "01109",
                "country": "US",
                "phone": "4137316700",
                "email": "labelgroup@comcast.net",
            },

            "order_number": order_number,
            "order_status": "AWAITPAY",
            "currency": "USD",
            "subtotal_price": money(order.subtotal),
            "shipping_cost": money(order.shipping_cost),
            "shipping_cost_currency": "USD",
            "total_price": money(order.total),
            "shipping_method": str(shipping_method)[:100],
            "line_items": line_items,

            "notes": (
                "THE LABEL GROUP website order #%s. "
                "Payment has not been collected by checkout."
            ) % order.pk,
        }

        headers = {
            "Authorization": "ShippoToken " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "SHIPPO-API-VERSION": "2018-02-08",
        }

        with requests.Session() as session:
            response = session.get(
                API + "/orders/",
                headers=headers,
                params={"results": 100, "page": 1},
                timeout=25,
            )
            response.raise_for_status()

            remote_id = None

            for remote in response.json().get("results", []):
                if str(remote.get("order_number", "")) == order_number:
                    remote_id = remote.get("object_id")
                    break

            if not remote_id:
                response = session.post(
                    API + "/orders/",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                response.raise_for_status()
                remote_id = response.json().get("object_id")

        if not remote_id:
            return False, "Shippo did not return an order ID."

        order.notes = (order.notes or "") + (
            "\n[SHIPPO_ORDER_ID:%s]" % remote_id
        )
        order.save(update_fields=["notes"])

        return True, "Synced to Shippo: " + str(remote_id)

    except requests.RequestException as exc:
        status = getattr(
            getattr(exc, "response", None), "status_code", ""
        )
        logger.warning(
            "Shippo sync failed for order %s. HTTP status: %s",
            order.pk, status
        )
        return False, "Shippo API request failed. Check server logs."

    except Exception:
        logger.exception(
            "Shippo sync failed for order %s.", order.pk
        )
        return False, "Unexpected Shippo sync error. Check server logs."
