from decimal import Decimal
import re

from django import forms
from django.contrib.auth.models import User

from products.models import Product
from .models import StaffProfile


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            "name",
            "product_code",
            "product_type",
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
            "product_code": "Product / Sticker Code",
            "product_type": "Product Type",
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

            "product_code": forms.TextInput(
                attrs={
                    "placeholder": "e.g. DGO, P001, G001 (optional)"
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
                    "min": "1",
                    "placeholder": "1.00"
                }
            ),

            "discount_price": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "1",
                    "placeholder": "1.00"
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

        minimum_price = Decimal("1.00")

        if price is not None and price < minimum_price:
            self.add_error(
                "price",
                "Price must be at least $1.00 USD."
            )

        if (
            discount_price is not None
            and discount_price < minimum_price
        ):
            self.add_error(
                "discount_price",
                "Discount price must be at least $1.00 USD."
            )

        if discount_price is not None and price is None:
            self.add_error(
                "discount_price",
                "Enter the regular price before setting a discount price."
            )

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


# =====================================================
# STRONG PASSWORD VALIDATION
# =====================================================

def validate_staff_password(password, username=None, full_name=None):

    if len(password) < 10:
        raise forms.ValidationError(
            "Password must contain at least 10 characters."
        )

    if not re.search(r"[A-Z]", password):
        raise forms.ValidationError(
            "Password must contain at least one uppercase letter."
        )

    if not re.search(r"[a-z]", password):
        raise forms.ValidationError(
            "Password must contain at least one lowercase letter."
        )

    if not re.search(r"\d", password):
        raise forms.ValidationError(
            "Password must contain at least one number."
        )

    if not re.search(r"[^A-Za-z0-9]", password):
        raise forms.ValidationError(
            "Password must contain at least one special character such as ! @ # $ %."
        )

    if username and username.lower() in password.lower():
        raise forms.ValidationError(
            "Password must not contain your username."
        )

    if full_name:
        name_parts = full_name.lower().split()

        for part in name_parts:
            if len(part) >= 3 and part in password.lower():
                raise forms.ValidationError(
                    "Password should not contain your name."
                )


# =====================================================
# STAFF REGISTRATION FORM
# =====================================================

class StaffRegistrationForm(forms.Form):

    full_name = forms.CharField(
        max_length=150,
        label="Full Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter your full name"
            }
        )
    )

    phone = forms.CharField(
        max_length=30,
        label="Phone Number",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter your phone number"
            }
        )
    )

    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter your email address"
            }
        )
    )

    username = forms.CharField(
        max_length=150,
        label="Username",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Choose a username"
            }
        )
    )

    role = forms.ChoiceField(
        choices=StaffProfile.ROLE_CHOICES,
        label="Requested Role"
    )

    password = forms.CharField(
        label="Strong Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Create a strong password",
                "autocomplete": "new-password"
            }
        ),
        help_text=(
            "Use at least 10 characters with uppercase and lowercase "
            "letters, a number and a special character."
        )
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm your strong password",
                "autocomplete": "new-password"
            }
        )
    )

    def clean_email(self):

        email = self.cleaned_data["email"]

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean_username(self):

        username = self.cleaned_data["username"]

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        username = cleaned_data.get("username")
        full_name = cleaned_data.get("full_name")

        if (
            password
            and confirm_password
            and password != confirm_password
        ):
            self.add_error(
                "confirm_password",
                "Passwords do not match."
            )

        if password:
            try:
                validate_staff_password(
                    password,
                    username=username,
                    full_name=full_name
                )
            except forms.ValidationError as error:
                self.add_error("password", error)

        return cleaned_data


# =====================================================
# BOSS CREATE STAFF FORM
# =====================================================

class OwnerStaffForm(forms.Form):

    full_name = forms.CharField(
        max_length=150,
        label="Full Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter staff full name"
            }
        )
    )

    phone = forms.CharField(
        max_length=30,
        label="Phone Number",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter phone number"
            }
        )
    )

    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter email address"
            }
        )
    )

    username = forms.CharField(
        max_length=150,
        label="Username",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Create username"
            }
        )
    )

    role = forms.ChoiceField(
        choices=StaffProfile.ROLE_CHOICES,
        label="Staff Role"
    )

    password = forms.CharField(
        label="Strong Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Create a strong password",
                "autocomplete": "new-password"
            }
        ),
        help_text=(
            "Use at least 10 characters with uppercase and lowercase "
            "letters, a number and a special character."
        )
    )

    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirm password",
                "autocomplete": "new-password"
            }
        )
    )

    def clean_email(self):

        email = self.cleaned_data["email"]

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean_username(self):

        username = self.cleaned_data["username"]

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        username = cleaned_data.get("username")
        full_name = cleaned_data.get("full_name")

        if (
            password
            and confirm_password
            and password != confirm_password
        ):
            self.add_error(
                "confirm_password",
                "Passwords do not match."
            )

        if password:
            try:
                validate_staff_password(
                    password,
                    username=username,
                    full_name=full_name
                )
            except forms.ValidationError as error:
                self.add_error("password", error)

        return cleaned_data