from pathlib import Path
from decimal import Decimal
import ast

path = Path("products/views.py")
source = path.read_text(encoding="utf-8-sig")

start_marker = "    def get_shippo_rates(address, packages):"
end_marker = "    items = get_items()"

if source.count(start_marker) != 1:
    raise SystemExit(
        "STOP: Expected exactly one get_shippo_rates function. "
        "No source changes were made."
    )

start = source.index(start_marker)
end = source.find(end_marker, start)

if end == -1:
    raise SystemExit(
        "STOP: Could not find the checkout items section after the rate function. "
        "No source changes were made."
    )

replacement = '''    def get_configured_shipping_rates(address, packages, order_subtotal):
        """
        Calculate store-configured shipping estimates.
        This is NOT a live UPS or Shippo rate.
        """
        from decimal import Decimal, InvalidOperation
        from .models import ShippingRule, ShippingSystemSettings

        if not packages:
            raise ValueError("No valid packages were provided for shipping.")

        settings = ShippingSystemSettings.objects.first()
        if not settings or not settings.enabled:
            raise ValueError(
                "Shipping is currently unavailable. Please contact us "
                "for a shipping quote."
            )

        total_weight = sum(
            (Decimal(str(package["weight"])) for package in packages),
            Decimal("0.00"),
        )
        subtotal_value = Decimal(str(order_subtotal))
        country = str(address.get("country", "")).strip().upper()
        state = str(address.get("state", "")).strip().upper()
        postal = str(address.get("zip", "")).strip().upper()

        def normalized_country(value):
            value = str(value or "").strip().upper()
            aliases = {
                "US": "US",
                "USA": "US",
                "UNITED STATES": "US",
                "UNITED STATES OF AMERICA": "US",
            }
            return aliases.get(value, value)

        matching_rules = []
        for rule in ShippingRule.objects.filter(active=True).order_by("-priority", "id"):
            rule_country = normalized_country(rule.country)
            if rule_country and rule_country != normalized_country(country):
                continue

            rule_state = str(rule.state or "").strip().upper()
            if rule_state and rule_state != state:
                continue

            prefix = str(rule.postal_prefix or "").strip().upper()
            if prefix and not postal.startswith(prefix):
                continue

            minimum = Decimal(str(rule.minimum_weight_lb or "0"))
            if total_weight < minimum:
                continue

            if rule.maximum_weight_lb is not None:
                maximum = Decimal(str(rule.maximum_weight_lb))
                if total_weight > maximum:
                    continue

            matching_rules.append(rule)

        rule = matching_rules[0] if matching_rules else None

        if rule:
            flat_fee = Decimal(str(rule.flat_fee))
            per_lb_fee = Decimal(str(rule.per_lb_fee))
            handling_fee = Decimal(str(rule.handling_fee))
            free_threshold = (
                Decimal(str(rule.free_shipping_threshold))
                if rule.free_shipping_threshold is not None else None
            )
            rate_id = "tlg-configured-rule-{}".format(rule.pk)
            service_name = rule.name or "Standard Shipping"
        else:
            flat_fee = Decimal(str(settings.default_flat_fee))
            per_lb_fee = Decimal(str(settings.default_per_lb_fee))
            handling_fee = Decimal(str(settings.default_handling_fee))
            free_threshold = (
                Decimal(str(settings.default_free_shipping_threshold))
                if settings.default_free_shipping_threshold is not None else None
            )
            rate_id = "tlg-configured-default"
            service_name = "Standard Shipping (Store Estimate)"

        if free_threshold is not None and free_threshold > 0 and subtotal_value >= free_threshold:
            amount = Decimal("0.00")
            service_name += " - Free"
        else:
            amount = flat_fee + (per_lb_fee * total_weight) + handling_fee

        amount = amount.quantize(Decimal("0.01"))

        return [{
            "object_id": rate_id,
            "provider": "The Label Group (Configured Estimate)",
            "service": service_name,
            "amount": str(amount),
            "currency": "USD",
            "estimated_days": None,
        }]

'''

updated = source[:start] + replacement + source[end:]

old_call = "get_shippo_rates(address, packages)"
if updated.count(old_call) != 1:
    raise SystemExit(
        "STOP: Expected exactly one rate-calculation call. "
        "No source changes were written."
    )

updated = updated.replace(
    old_call,
    "get_configured_shipping_rates(address, packages, subtotal)",
    1,
)

updated = updated.replace(
    "Shippo rate ID: {}. Shipping amount: ${} USD.",
    "Rate reference: {}. Shipping amount: ${} USD.",
    1,
)

# The configured rate is not a purchased carrier label.
ast.parse(updated)
path.write_text(updated, encoding="utf-8")
print("Checkout shipping calculation updated.")
print("Configured rules and default rates are now used by checkout.")
print("No database records were modified.")
