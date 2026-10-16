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
