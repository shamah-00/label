from django import forms
from .models import (
    Product,
    QuoteRequest,
    CollectionCalendarStickerOrder,
)


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            "name",
            "slug",
            "description",
            "category",
            "industry",
            "brand",
            "price",
            "discount_price",
            "image",
            "stock",
            "material",
            "finish",
            "shape",
            "printing_method",
            "adhesive",
            "is_custom",
            "is_available",
            "is_featured",
        ]

        labels = {
            "name": "Product Name",
            "slug": "Product URL Name",
            "description": "Product Description",
            "category": "Category",
            "industry": "Customer / Industry",
            "brand": "Brand",
            "price": "Price (USD)",
            "discount_price": "Discount Price (USD)",
            "image": "Product Image",
            "stock": "Stock",
            "material": "Material",
            "finish": "Finish",
            "shape": "Shape",
            "printing_method": "Printing Method",
            "adhesive": "Adhesive / Application",
            "is_custom": "Custom Product",
            "is_available": "Available on Website",
            "is_featured": "Featured Product",
        }

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter product name"
                }
            ),

            "slug": forms.TextInput(
                attrs={
                    "placeholder": "product-url-name"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Describe the product..."
                }
            ),

            "brand": forms.TextInput(
                attrs={
                    "placeholder": "Brand name (optional)"
                }
            ),

            "price": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00"
                }
            ),

            "discount_price": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00"
                }
            ),

            "stock": forms.NumberInput(
                attrs={
                    "min": "0"
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        price = cleaned_data.get("price")
        discount_price = cleaned_data.get("discount_price")

        if (
            price is not None
            and discount_price is not None
            and discount_price > price
        ):
            self.add_error(
                "discount_price",
                "Discount price cannot be higher than the regular price."
            )

        return cleaned_data


class QuoteRequestForm(forms.ModelForm):

    class Meta:
        model = QuoteRequest

        fields = [
            "customer_name",
            "company_name",
            "customer_email",
            "customer_phone",
            "street_address",
            "address_continued",
            "city",
            "state",
            "postal_code",
            "country",
            "requirements",
            "uploaded_file",
        ]

        labels = {
            "customer_name": "Full Name",
            "company_name": "Company Name",
            "customer_email": "Email Address",
            "customer_phone": "Phone Number",
            "street_address": "Street Address",
            "address_continued": "Address Continued",
            "city": "City",
            "state": "State",
            "postal_code": "Postal Code",
            "country": "Country",
            "requirements": "Requirements / Special Instructions",
            "uploaded_file": "Reference File",
        }

        widgets = {
            "customer_name": forms.TextInput(
                attrs={
                    "placeholder": "Your full name"
                }
            ),

            "company_name": forms.TextInput(
                attrs={
                    "placeholder": "Company name"
                }
            ),

            "customer_email": forms.EmailInput(
                attrs={
                    "placeholder": "you@example.com"
                }
            ),

            "customer_phone": forms.TextInput(
                attrs={
                    "placeholder": "Phone number"
                }
            ),

            "street_address": forms.TextInput(
                attrs={
                    "placeholder": "Street address"
                }
            ),

            "address_continued": forms.TextInput(
                attrs={
                    "placeholder": "Apartment, suite, building, etc. (optional)"
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "placeholder": "City"
                }
            ),

            "state": forms.TextInput(
                attrs={
                    "placeholder": "State / County / Region"
                }
            ),

            "postal_code": forms.TextInput(
                attrs={
                    "placeholder": "Postal code"
                }
            ),

            "country": forms.TextInput(
                attrs={
                    "placeholder": "Country"
                }
            ),

            "requirements": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": (
                        "Tell us about the stickers or decals you need, "
                        "quantities, sizes, materials, finishes, artwork, "
                        "or any other requirements."
                    )
                }
            ),

            "uploaded_file": forms.ClearableFileInput(
                attrs={
                    "accept": ".jpg,.jpeg,.png,.pdf,.ai,.eps,.svg,.zip"
                }
            ),
        }


class CollectionCalendarStickerOrderForm(forms.ModelForm):

    class Meta:
        model = CollectionCalendarStickerOrder

        fields = [
            "calendar_year",
            "trash_collection_day",
            "trash_collection_frequency",
            "other_trash_frequency",
            "recycling_collection_day",
            "recycling_collection_frequency",
            "other_recycling_frequency",
            "new_years_day",
            "memorial_day",
            "independence_day",
            "labor_day",
            "thanksgiving_day",
            "christmas_day",
            "other_holiday_1",
            "other_holiday_2",
            "other_holiday_3",
            "top_bar_color",
            "include_company_logo",
            "other_collection_information",
            "quantity",
            "name",
            "title",
            "company",
            "street_address",
            "address_contd",
            "city",
            "state",
            "zip_code",
            "phone",
            "email",
        ]

        labels = {
            "calendar_year": "Calendar Year",
            "trash_collection_day": "Trash Collection Day",
            "trash_collection_frequency": "Trash Collection Frequency",
            "other_trash_frequency": "Specify Other Trash Frequency",
            "recycling_collection_day": "Recycling Collection Day",
            "recycling_collection_frequency": "Recycling Collection Frequency",
            "other_recycling_frequency": "Specify Other Recycling Frequency",
            "new_years_day": "New Year's Day",
            "memorial_day": "Memorial Day",
            "independence_day": "Independence Day (July 4)",
            "labor_day": "Labor Day",
            "thanksgiving_day": "Thanksgiving Day",
            "christmas_day": "Christmas Day",
            "other_holiday_1": "Other Holiday 1",
            "other_holiday_2": "Other Holiday 2",
            "other_holiday_3": "Other Holiday 3",
            "top_bar_color": "Color of Top Bar",
            "include_company_logo": "Include Company Logo?",
            "other_collection_information": "Other Collection Information",
            "quantity": "Quantity",
            "name": "Name",
            "title": "Title",
            "company": "Company",
            "street_address": "Street Address",
            "address_contd": "Address Continued",
            "city": "City",
            "state": "State",
            "zip_code": "Zip",
            "phone": "Phone",
            "email": "E-mail",
        }

        widgets = {
            "calendar_year": forms.Select(),

            "other_trash_frequency": forms.TextInput(
                attrs={
                    "placeholder": "Please specify"
                }
            ),

            "other_recycling_frequency": forms.TextInput(
                attrs={
                    "placeholder": "Please specify"
                }
            ),

            "other_holiday_1": forms.TextInput(
                attrs={
                    "placeholder": "Other holiday"
                }
            ),

            "other_holiday_2": forms.TextInput(
                attrs={
                    "placeholder": "Other holiday"
                }
            ),

            "other_holiday_3": forms.TextInput(
                attrs={
                    "placeholder": "Other holiday"
                }
            ),

            "other_collection_information": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Enter any other collection information"
                }
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "min": "1000",
                    "step": "1",
                    "placeholder": "Minimum 1000"
                }
            ),

            "name": forms.TextInput(
                attrs={
                    "placeholder": "Your name"
                }
            ),

            "title": forms.TextInput(
                attrs={
                    "placeholder": "Your title"
                }
            ),

            "company": forms.TextInput(
                attrs={
                    "placeholder": "Company name"
                }
            ),

            "street_address": forms.TextInput(
                attrs={
                    "placeholder": "Street address"
                }
            ),

            "address_contd": forms.TextInput(
                attrs={
                    "placeholder": "Apartment, suite, building, etc."
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "placeholder": "City"
                }
            ),

            "state": forms.TextInput(
                attrs={
                    "placeholder": "State"
                }
            ),

            "zip_code": forms.TextInput(
                attrs={
                    "placeholder": "Zip code"
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "placeholder": "Phone number"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "you@example.com"
                }
            ),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")

        if quantity is None:
            return quantity

        if quantity < 1000:
            raise forms.ValidationError(
                "The minimum quantity is 1000 stickers."
            )

        return quantity

    def clean(self):
        cleaned_data = super().clean()

        trash_frequency = cleaned_data.get(
            "trash_collection_frequency"
        )
        other_trash = cleaned_data.get(
            "other_trash_frequency"
        )

        if trash_frequency == "other" and not other_trash:
            self.add_error(
                "other_trash_frequency",
                "Please specify the other trash collection frequency."
            )

        recycling_frequency = cleaned_data.get(
            "recycling_collection_frequency"
        )
        other_recycling = cleaned_data.get(
            "other_recycling_frequency"
        )

        if recycling_frequency == "other" and not other_recycling:
            self.add_error(
                "other_recycling_frequency",
                "Please specify the other recycling collection frequency."
            )

        return cleaned_data