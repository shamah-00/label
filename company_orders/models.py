from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class KnownCompany(models.Model):
    name = models.CharField(max_length=200, unique=True)
    historical_item_count = models.PositiveIntegerField(default=0)
    historical_avg_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Known company"
        verbose_name_plural = "Known companies"

    def __str__(self):
        return self.name


class CompanyOrderRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending staff review"),
        ("approved", "Approved"),
        ("countered", "Counteroffer required"),
        ("rejected", "Rejected"),
    ]

    company = models.ForeignKey(
        KnownCompany, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="requests"
    )
    company_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)

    # Retained for compatibility with existing requests and integrations.
    # For new multi-product requests, these fields mirror the first item.
    product = models.ForeignKey(
        "products.Product", on_delete=models.SET_NULL,
        related_name="company_order_requests",
        null=True, blank=True,
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    requested_unit_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Requested unit price in USD. Not an approved price."
    )

    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    staff_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Company order request"
        verbose_name_plural = "Company order requests"

    @property
    def requested_total(self):
        items = list(self.items.all())
        if items:
            return sum(
                (item.requested_total for item in items),
                Decimal("0.00"),
            )
        return self.quantity * self.requested_unit_price

    def __str__(self):
        return f"{self.company_name} - request #{self.pk} - {self.status}"


class CompanyOrderItem(models.Model):
    order_request = models.ForeignKey(
        CompanyOrderRequest,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        related_name="company_order_items",
        null=True,
        blank=True,
    )
    custom_description = models.TextField(
        blank=True,
        help_text="Customer description when the requested item is CUSTOM.",
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    requested_unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Customer-requested USD price, not an approved price.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Company order item"
        verbose_name_plural = "Company order items"

    @property
    def requested_total(self):
        return self.quantity * self.requested_unit_price

    def __str__(self):
        name = self.custom_description if not self.product else str(self.product)
        return f"{name or 'Custom product'} x {self.quantity}"
