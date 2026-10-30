from django.core.management.base import BaseCommand
from products.models import Order
from products.shippo_orders import sync_order_to_shippo


class Command(BaseCommand):
    help = "Sync existing unshipped orders to Shippo."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        orders = Order.objects.exclude(
            status__in=["cancelled", "shipped", "completed"]
        ).order_by("created_at")

        checked = 0
        synced = 0
        failed = 0

        for order in orders.iterator():
            shipment = getattr(order, "shipment", None)

            if shipment and (
                shipment.label_url or shipment.shippo_transaction_id
            ):
                continue

            if "[SHIPPO_ORDER_ID:" in (order.notes or ""):
                self.stdout.write(
                    "Already synced: order #%s" % order.pk
                )
                continue

            checked += 1

            if options["dry_run"]:
                self.stdout.write(
                    "Would sync order #%s" % order.pk
                )
                continue

            ok, message = sync_order_to_shippo(order)

            if ok:
                synced += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        "Order #%s: %s" % (order.pk, message)
                    )
                )
            else:
                failed += 1
                self.stderr.write(
                    self.style.ERROR(
                        "Order #%s: %s" % (order.pk, message)
                    )
                )

        self.stdout.write(
            "Checked: %s | Synced: %s | Failed: %s"
            % (checked, synced, failed)
        )
