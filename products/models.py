from django.conf import settings as django_conf_settings
from django.utils.text import slugify
from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):

    CATEGORY_CHOICES = [
        ("decals", "Decals"),
        ("stickers", "Stickers"),
        ("reflective", "Reflective Products"),
        ("custom", "Custom Products"),
        ("other", "Other"),
    ]

    INDUSTRY_CHOICES = [
        ("truck_motor_car", "Truck / Motor / Car Decals"),
        ("government", "Government Contractor Decals"),
        ("pool", "Pool Decals"),
        ("construction", "Construction Decals"),
        ("waste", "Waste Company Decals"),
    ]

    MATERIAL_CHOICES = [
        ("vinyl", "Vinyl"),
        ("paper", "Paper"),
        ("mylar", "Mylar"),
        ("polystyrene", "Polystyrene"),
        ("other", "Other / Specify in Notes"),
    ]

    SHAPE_CHOICES = [
        ("rectangle", "Rectangle"),
        ("square", "Square"),
        ("circle", "Circle"),
        ("oval", "Oval"),
        ("custom", "Custom / Die-cut"),
    ]

    FINISH_CHOICES = [
        ("gloss", "Gloss"),
        ("matte", "Matte"),
        ("satin", "Satin"),
        ("clear", "Clear"),
        ("other", "Other / Specify in Notes"),
    ]

    PRINTING_METHOD_CHOICES = [
        ("full_color", "Full Color"),
        ("black_white", "Black & White"),
        ("single_sided", "Single-Sided"),
        ("double_sided", "Double-Sided"),
        ("digital", "Digital Printing"),
        ("screen", "Screen Printing"),
    ]

    ADHESIVE_CHOICES = [
        ("permanent", "Permanent"),
        ("removable", "Removable"),
        ("indoor", "Indoor"),
        ("outdoor", "Outdoor"),
        ("not_applicable", "Not Applicable"),
    ]

    PRODUCT_NAME_CHOICES = [
        ("bag_tag", "Bag & Tag Sticker"),
        ("container_decal", "Container Identification Decal"),
        ("dumpster_decal", "Dumpster Identification Decal"),
        ("baler_decal", "Baler Decal"),
        ("compactor_decal", "Compactor Decal"),
        ("rolloff_decal", "Rolloff Decal"),
        ("recycling_label", "Recycling Label"),
        ("truck_decal", "Truck Decal"),
        ("fleet_decal", "Fleet Decal"),
        ("yard_waste_label", "Yard Waste Label"),
        ("safety_decal", "Safety & Compliance Decal"),
        ("reflective_label", "Reflective Label"),
        ("facility_sign", "Facility Sign"),
        ("food_waste_label", "Food Waste Label"),
        ("medical_waste_label", "Medical Waste Label"),
        ("portable_toilet_decal", "Portable Toilet Decal"),
        ("custom_label", "Custom Label"),
        ("other", "Other / New Product"),
    ]

    name = models.CharField(
        max_length=200
    )

    product_code = models.CharField(
        max_length=50,
        blank=True
    )

    product_type = models.CharField(
        max_length=100,
        choices=PRODUCT_NAME_CHOICES,
        default="other"
    )

    slug = models.SlugField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
        default="other"
    )

    industry = models.CharField(
        max_length=100,
        choices=INDUSTRY_CHOICES,
        default="waste"
    )

    brand = models.CharField(
        max_length=100,
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    material = models.CharField(
        max_length=100,
        choices=MATERIAL_CHOICES,
        blank=True
    )

    finish = models.CharField(
        max_length=100,
        choices=FINISH_CHOICES,
        blank=True
    )

    shape = models.CharField(
        max_length=100,
        choices=SHAPE_CHOICES,
        blank=True
    )

    printing_method = models.CharField(
        max_length=100,
        choices=PRINTING_METHOD_CHOICES,
        blank=True
    )

    adhesive = models.CharField(
        max_length=100,
        choices=ADHESIVE_CHOICES,
        blank=True
    )

    PACKAGE_TYPE_CHOICES = [
        ("", "Not Set"),
        ("box", "Box - Roll Labels"),
        ("flat_mailer", "Flat Mailer - Decal Sheets"),
        ("tube", "Tube - Large Vinyl Graphics"),
    ]

    # Shipping measurements are stored in pounds and inches.
    # Leave values empty until the actual packed product is measured.
    packaging_type = models.CharField(
        max_length=20,
        choices=PACKAGE_TYPE_CHOICES,
        blank=True,
        default="",
    )

    shipping_weight_lb = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    shipping_length_in = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    shipping_width_in = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    shipping_height_in = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    is_custom = models.BooleanField(
        default=False
    )

    is_available = models.BooleanField(
        default=True
    )

    is_featured = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from django.db import IntegrityError, transaction

        base_slug = (self.slug or "").strip()
        if not base_slug:
            base_slug = slugify(getattr(self, "name", "") or getattr(self, "title", "") or "product")
        base_slug = base_slug or "product"

        candidate = base_slug
        counter = 2

        ProductModel = self.__class__
        while ProductModel.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            candidate = f"{base_slug}-{counter}"
            counter += 1

        self.slug = candidate
        return super().save(*args, **kwargs)

class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("packed", "Packed"),
        ("shipped", "Shipped"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    customer_name = models.CharField(
        max_length=200
    )

    customer_email = models.EmailField()

    customer_phone = models.CharField(
        max_length=50
    )

    shipping_address = models.TextField()

    shipping_city = models.CharField(
        max_length=100
    )

    shipping_state = models.CharField(
        max_length=100,
        blank=True
    )

    shipping_postal_code = models.CharField(
        max_length=30,
        blank=True
    )

    shipping_country = models.CharField(
        max_length=100
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    currency = models.CharField(
        max_length=3,
        default="USD"
    )

    PAYMENT_METHOD_CHOICES = [
        ("upfront", "Pay Upfront"),
        ("check", "Check / Invoice"),
        ("card", "Credit Card"),
        ("ach", "ACH Bank Transfer"),
        ("wire", "Wire Transfer"),
    ]

    PAYMENT_TERMS_CHOICES = [
        (0, "Due on Receipt"),
        (30, "Net 30 Days"),
        (45, "Net 45 Days"),
        (60, "Net 60 Days"),
        (90, "Net 90 Days"),
    ]

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="upfront",
    )

    payment_terms_days = models.PositiveSmallIntegerField(
        choices=PAYMENT_TERMS_CHOICES,
        default=0,
    )

    credit_terms_approved = models.BooleanField(
        default=False,
        help_text="Enable only for customers approved for business credit terms.",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending"
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items"
    )

    product_name = models.CharField(
        max_length=200
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )

    currency = models.CharField(
        max_length=3,
        default="USD"
    )

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class Shipment(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Preparing Shipment"),
        ("packed", "Packed"),
        ("shipped", "Shipped"),
        ("in_transit", "In Transit"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("delayed", "Delayed"),
        ("returned", "Returned"),
        ("cancelled", "Cancelled"),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="shipment"
    )

    carrier = models.CharField(
        max_length=100,
        blank=True
    )

    shipping_method = models.CharField(
        max_length=100,
        blank=True
    )

    tracking_number = models.CharField(
        max_length=200,
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending"
    )

    estimated_delivery = models.DateField(
        null=True,
        blank=True
    )

    shipped_at = models.DateTimeField(
        null=True,
        blank=True
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )
    shippo_rate_id = models.CharField(max_length=200, blank=True)
    shippo_transaction_id = models.CharField(max_length=200, blank=True)
    label_url = models.URLField(max_length=1000, blank=True)
    tracking_url = models.URLField(max_length=1000, blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Shipment for Order #{self.order.id}"




class Invoice(models.Model):
    STATUS_CHOICES = [
        ("unpaid", "Unpaid"),
        ("partial", "Partially Paid"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
    ]

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="invoice",
    )
    invoice_number = models.CharField(max_length=40, unique=True, blank=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    currency = models.CharField(max_length=3, default="USD")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="unpaid",
    )
    terms_days = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-invoice_date", "-id"]

    @property
    def balance_due(self):
        return max(self.total - self.amount_paid, 0)

    def save(self, *args, **kwargs):
        from django.utils import timezone

        if self.order_id and not self.invoice_number:
            year = self.invoice_date.year if self.invoice_date else timezone.localdate().year
            self.invoice_number = f"TLG-{year}-{self.order_id:06d}"

        if self.total > 0 and self.amount_paid >= self.total:
            self.status = "paid"
        elif self.amount_paid > 0:
            self.status = "partial"
        elif self.due_date and self.due_date < timezone.localdate():
            self.status = "overdue"
        else:
            self.status = "unpaid"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number or f"Invoice for Order #{self.order_id}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    description = models.CharField(max_length=250)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.description} x {self.quantity}"

class StaffProfile(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staff_profile"
    )

    full_name = models.CharField(
        max_length=200
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.full_name} - {self.get_status_display()}"


class QuoteRequest(models.Model):

    STATUS_CHOICES = [
        ("new", "New"),
        ("reviewing", "Being Reviewed"),
        ("quoted", "Quote Sent"),
        ("approved", "Approved"),
        ("in_production", "In Production"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    customer_name = models.CharField(
        max_length=200
    )

    company_name = models.CharField(
        max_length=200,
        blank=True
    )

    customer_email = models.EmailField()

    customer_phone = models.CharField(
        max_length=50
    )

    street_address = models.CharField(
        max_length=255,
        blank=True
    )

    address_continued = models.CharField(
        max_length=255,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    postal_code = models.CharField(
        max_length=30,
        blank=True
    )

    country = models.CharField(
        max_length=100,
        blank=True
    )

    requirements = models.TextField(
        blank=True
    )

    uploaded_file = models.FileField(
        upload_to="quote_requests/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="new"
    )

    staff_notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Quote #{self.id} - {self.customer_name}"


class QuoteRequestItem(models.Model):

    quote_request = models.ForeignKey(
        QuoteRequest,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="quote_request_items"
    )

    product_name = models.CharField(
        max_length=200
    )

    product_code = models.CharField(
        max_length=50,
        blank=True
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class CollectionCalendarStickerOrder(models.Model):

    YEAR_CHOICES = [
        (year, str(year))
        for year in range(2027, 2101)
    ]

    DAY_CHOICES = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
    ]

    FREQUENCY_CHOICES = [
        ("Once per week", "Once per week"),
        ("Every other week", "Every other week"),
        ("Once per month", "Once per month"),
        ("Other", "Other"),
    ]

    COLOR_CHOICES = [
        ("Green", "Green"),
        ("Red", "Red"),
        ("Blue", "Blue"),
        ("Yellow", "Yellow"),
        ("Orange", "Orange"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    calendar_year = models.PositiveIntegerField(
        choices=YEAR_CHOICES
    )

    trash_collection_day = models.CharField(
        max_length=20,
        choices=DAY_CHOICES
    )

    trash_collection_frequency = models.CharField(
        max_length=50,
        choices=FREQUENCY_CHOICES
    )

    other_trash_frequency = models.CharField(
        max_length=255,
        blank=True
    )

    recycling_collection_day = models.CharField(
        max_length=20,
        choices=DAY_CHOICES
    )

    recycling_collection_frequency = models.CharField(
        max_length=50,
        choices=FREQUENCY_CHOICES
    )

    other_recycling_frequency = models.CharField(
        max_length=255,
        blank=True
    )

    new_years_day = models.BooleanField(
        default=False
    )

    memorial_day = models.BooleanField(
        default=False
    )

    independence_day = models.BooleanField(
        default=False
    )

    labor_day = models.BooleanField(
        default=False
    )

    thanksgiving_day = models.BooleanField(
        default=False
    )

    christmas_day = models.BooleanField(
        default=False
    )

    other_holiday_1 = models.CharField(
        max_length=255,
        blank=True
    )

    other_holiday_2 = models.CharField(
        max_length=255,
        blank=True
    )

    other_holiday_3 = models.CharField(
        max_length=255,
        blank=True
    )

    top_bar_color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES
    )

    include_company_logo = models.BooleanField(
        default=False
    )

    other_collection_information = models.TextField(
        blank=True
    )

    quantity = models.PositiveIntegerField()

    name = models.CharField(
        max_length=200
    )

    title = models.CharField(
        max_length=200,
        blank=True
    )

    company = models.CharField(
        max_length=200
    )

    street_address = models.CharField(
        max_length=255
    )

    address_contd = models.CharField(
        max_length=255,
        blank=True
    )

    city = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    zip_code = models.CharField(
        max_length=30
    )

    phone = models.CharField(
        max_length=50,
        blank=True
    )

    email = models.EmailField()

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="new"
    )

    staff_notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.company} - {self.calendar_year} - {self.quantity} stickers"
class SiteSettings(models.Model):
    company_name = models.CharField(max_length=200, default="THE LABEL GROUP")
    tagline = models.CharField(max_length=255, default="INDUSTRIAL PRINTS & DECALS")
    phone = models.CharField(max_length=100, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    whatsapp = models.CharField(max_length=100, blank=True, default="")
    facebook = models.URLField(blank=True, default="")
    instagram = models.URLField(blank=True, default="")
    tiktok = models.URLField(blank=True, default="")
    linkedin = models.URLField(blank=True, default="")
    youtube = models.URLField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

    @classmethod
    def get_settings(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create(
                company_name="THE LABEL GROUP",
                tagline="INDUSTRIAL PRINTS & DECALS"
            )
        return obj



    def get_intro_description(self):
        if not self.description:
            return ""
        return self.description.split('\n\n')[0].strip()

    def get_spec_table(self):
        specs = []
        if not self.description:
            return specs
        lines = self.description.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-'):
                line = line[1:].strip()
            if ':' in line:
                parts = line.split(':', 1)
                specs.append({'key': parts[0].strip(), 'value': parts[1].strip()})
        return specs


class ShippingRule(models.Model):
    """Configurable shipping rate. Monetary amounts are stored in USD."""
    name = models.CharField(max_length=120, unique=True)
    country = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    postal_prefix = models.CharField(max_length=30, blank=True, default="")
    flat_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_lb_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    handling_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free_shipping_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    minimum_weight_lb = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    maximum_weight_lb = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    priority = models.PositiveIntegerField(default=100)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "name"]

    def __str__(self):
        return self.name


class ShippingSystemSettings(models.Model):
    """Global shipping defaults managed by authorized staff."""
    enabled = models.BooleanField(default=True)
    default_flat_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=15
    )
    default_per_lb_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=1
    )
    default_handling_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    default_free_shipping_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    default_weight_lb = models.DecimalField(
        max_digits=10, decimal_places=2, default=1
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "The Label Group shipping settings"

    @classmethod
    def get_settings(cls):
        obj = cls.objects.first()
        if obj is None:
            obj = cls.objects.create()
        return obj


def _tlg_default_payment_methods():
    return ["square", "quickbooks", "check", "ach", "wire"]


class PaymentSystemSettings(models.Model):
    """Business-controlled payment preferences. No card or bank credentials stored."""

    PAYMENT_TIMING_CHOICES = [
        ("upfront", "Request payment before processing"),
        ("invoice_after_delivery", "Invoice after delivery"),
    ]

    TERMS_CHOICES = [
        (0, "Due on Receipt"),
        (30, "Net 30 Days"),
        (45, "Net 45 Days"),
        (60, "Net 60 Days"),
        (90, "Net 90 Days"),
    ]

    enabled_methods = models.JSONField(default=_tlg_default_payment_methods)
    payment_timing = models.CharField(
        max_length=30,
        choices=PAYMENT_TIMING_CHOICES,
        default="invoice_after_delivery",
    )
    default_terms_days = models.PositiveSmallIntegerField(
        choices=TERMS_CHOICES,
        default=30,
    )
    check_instructions = models.TextField(
        blank=True,
        default="Contact The Label Group for approved check and invoice instructions.",
    )
    ach_instructions = models.TextField(
        blank=True,
        default="Contact The Label Group for verified ACH payment instructions.",
    )
    wire_instructions = models.TextField(
        blank=True,
        default="Contact The Label Group for verified wire transfer instructions.",
    )
    square_payment_url = models.URLField(
        blank=True,
        max_length=500,
        help_text="HTTPS Square payment link created by the business owner.",
    )
    square_instructions = models.TextField(
        blank=True,
        default="",
        help_text="Customer-facing instructions for Square payments.",
    )
    quickbooks_payment_url = models.URLField(
        blank=True,
        max_length=500,
        help_text="HTTPS QuickBooks payment link created by the business owner.",
    )
    quickbooks_instructions = models.TextField(
        blank=True,
        default="",
        help_text="Customer-facing instructions for QuickBooks payments.",
    )
    updated_by = models.ForeignKey(
        django_conf_settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tlg_payment_settings_updates",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment System Settings"
        verbose_name_plural = "Payment System Settings"

    def __str__(self):
        return "The Label Group payment settings"

    @classmethod
    def get_settings(cls):
        obj = cls.objects.order_by("pk").first()
        if obj is None:
            obj = cls.objects.create()
        return obj

# QuickBooks OAuth connection model.
from .quickbooks_models import QuickBooksConnection
