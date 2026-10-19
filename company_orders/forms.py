from django import forms


class CompanyOrderRequestForm(forms.Form):
    company_name = forms.CharField(
        max_length=200,
        label="Company name",
        widget=forms.TextInput(attrs={
            "placeholder": "Enter your company name",
            "autocomplete": "organization",
        }),
    )
    contact_name = forms.CharField(
        max_length=150,
        label="Contact person",
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    email = forms.EmailField(
        label="Business email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    phone = forms.CharField(
        max_length=40,
        required=False,
        label="Phone number",
        widget=forms.TextInput(attrs={"autocomplete": "tel"}),
    )
    notes = forms.CharField(
        required=False,
        label="Additional information",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Describe sizes, materials, deadlines, or other requirements.",
        }),
    )

    def clean_company_name(self):
        return " ".join(self.cleaned_data["company_name"].split())
