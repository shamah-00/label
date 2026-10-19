from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "category",
        "material",
        "finish",
        "is_custom",
        "is_available",
        "is_featured",
        "created_at",
    )

    list_filter = (
        "category",
        "material",
        "finish",
        "is_custom",
        "is_available",
        "is_featured",
    )

    search_fields = (
        "name",
        "description",
        "brand",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }

    ordering = (
        "-created_at",
    )

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        shipping_fields = [
            'packaging_type',
            'shipping_weight_lb',
            'shipping_length_in',
            'shipping_width_in',
            'shipping_height_in',
        ]
        return fields + [name for name in shipping_fields if name not in fields]


from .models import ShippingRule, ShippingSystemSettings

@admin.register(ShippingRule)
class ShippingRuleAdmin(admin.ModelAdmin):
    list_display = (
        "name", "country", "state", "flat_fee", "per_lb_fee",
        "handling_fee", "active", "priority"
    )
    list_filter = ("active", "country")
    search_fields = ("name", "country", "state", "postal_prefix")
    list_editable = ("active", "priority")
    ordering = ("priority", "name")


@admin.register(ShippingSystemSettings)
class ShippingSystemSettingsAdmin(admin.ModelAdmin):
    list_display = ("enabled", "default_flat_fee", "default_per_lb_fee", "updated_at")


from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ("description", "quantity", "unit_price", "line_total")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number", "order", "invoice_date", "due_date",
        "total", "amount_paid", "status",
    )
    list_filter = ("status", "invoice_date", "due_date", "terms_days")
    search_fields = (
        "invoice_number", "order__customer_name", "order__customer_email",
    )
    readonly_fields = (
        "invoice_number", "order", "invoice_date", "due_date",
        "currency", "total", "terms_days", "created_at", "updated_at",
    )
    fields = (
        "invoice_number", "order", "invoice_date", "due_date",
        "currency", "total", "amount_paid", "status", "terms_days",
        "created_at", "updated_at",
    )
    inlines = [InvoiceItemInline]

    def save_model(self, request, obj, form, change):
        if obj.amount_paid < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError("Amount paid cannot be negative.")
        if obj.amount_paid > obj.total:
            from django.core.exceptions import ValidationError
            raise ValidationError("Amount paid cannot exceed the invoice total.")
        super().save_model(request, obj, form, change)
