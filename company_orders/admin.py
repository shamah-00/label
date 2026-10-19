from django.contrib import admin
from .models import KnownCompany, CompanyOrderRequest, CompanyOrderItem


@admin.register(KnownCompany)
class KnownCompanyAdmin(admin.ModelAdmin):
    list_display = (
        "name", "historical_item_count", "historical_avg_price", "is_active"
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)
    ordering = ("name",)


class CompanyOrderItemInline(admin.TabularInline):
    model = CompanyOrderItem
    extra = 0
    fields = ("product", "custom_description", "quantity", "requested_unit_price")
    readonly_fields = ()
    show_change_link = True


@admin.register(CompanyOrderRequest)
class CompanyOrderRequestAdmin(admin.ModelAdmin):
    list_display = (
        "company_name", "item_summary", "status", "created_at"
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "company_name", "contact_name", "email",
        "product__name", "items__product__name", "items__custom_description",
    )
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("status",)
    inlines = (CompanyOrderItemInline,)
    fieldsets = (
        ("Company contact", {
            "fields": ("company", "company_name", "contact_name", "email", "phone")
        }),
        ("Legacy first-item fields", {
            "fields": ("product", "quantity", "requested_unit_price", "notes"),
            "description": "For new requests, review all requested items in the items section below.",
        }),
        ("Staff decision", {
            "fields": ("status", "staff_response", "created_at", "updated_at")
        }),
    )

    @admin.display(description="Requested items")
    def item_summary(self, obj):
        items = list(obj.items.select_related("product").all())
        if not items:
            name = str(obj.product) if obj.product else "Custom product"
            return f"{name} ? {obj.quantity}"
        return "; ".join(
            f"{item.product if item.product else (item.custom_description or 'Custom product')} "
            f"? {item.quantity} @ ${item.requested_unit_price}"
            for item in items[:4]
        ) + (f" ? (+{len(items) - 4})" if len(items) > 4 else "")


@admin.register(CompanyOrderItem)
class CompanyOrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order_request", "product", "custom_description",
        "quantity", "requested_unit_price",
    )
    search_fields = (
        "order_request__company_name", "product__name",
        "custom_description", "order_request__email",
    )
    list_select_related = ("order_request", "product")
