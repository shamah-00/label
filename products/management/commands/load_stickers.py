# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from products.models import Product

PRODUCTS = [
    # ============================================================
    # GOVERNMENT (Example showing clear newline formatting)
    # ============================================================
    {
        "code": "G020",
        "name": "CUI/Controlled Unclassified Information",
        "industry": "government_contracting",
        "category": "stickers",
        "product_type": "government_decal",
        "description": "Government information-security label identifying media or materials containing Controlled Unclassified Information.\n\n- Standard Size: 2.125\" x 1.25\" landscape\n- Ideal Material: Industrial-grade polyester or approved media-label stock\n- Finish: Matte\n- Primary Application: Government documents, electronic media, storage devices, equipment, and CUI-controlled materials\n- Buyer's Notes: Use only for applications where the customer is authorized to apply CUI markings.",
    },
]

class Command(BaseCommand):
    help = "Safely loads product catalog descriptions with clean newlines"

    def handle(self, *args, **options):
        with transaction.atomic():
            for p_data in PRODUCTS:
                unique_slug = slugify(f"{p_data['code']}-{p_data['name']}")
                Product.objects.update_or_create(
                    product_code=p_data["code"],
                    defaults={
                        "name": p_data["name"],
                        "slug": unique_slug,
                        "industry": p_data["industry"],
                        "category": p_data["category"],
                        "product_type": p_data["product_type"],
                        "description": p_data["description"],
                    }
                )
        self.stdout.write(self.style.SUCCESS("Successfully updated product descriptions with clean formatting!"))
