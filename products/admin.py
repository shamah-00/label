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