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

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Shipment for Order #{self.order.id}"


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