from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Category, MenuItem

MAX_IMAGE_MB = 2


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Contoh: Kopi", "autofocus": True}
            )
        }
        error_messages = {"name": {"unique": "Kategori ini sudah ada."}}

    def clean_name(self):
        return self.cleaned_data["name"].strip()


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["name", "category", "price", "stock", "description", "is_available", "image"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Contoh: Es Kopi Susu Aren", "autofocus": True}
            ),
            "category": forms.Select(attrs={"class": "input"}),
            "price": forms.NumberInput(
                attrs={"class": "input", "min": 1000, "step": 500, "placeholder": "25000",
                       "data-price-input": True}
            ),
            "stock": forms.NumberInput(attrs={"class": "input", "min": 0}),
            "description": forms.Textarea(
                attrs={"class": "input", "rows": 3, "placeholder": "Satu-dua kalimat singkat tentang menu ini"}
            ),
            "image": forms.FileInput(attrs={"accept": "image/*", "data-image-input": True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].empty_label = "Pilih kategori"

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_image(self):
        image = self.cleaned_data.get("image")
        # Hanya validasi saat ada file baru yang diunggah
        if image and hasattr(image, "size") and image.size > MAX_IMAGE_MB * 1024 * 1024:
            raise forms.ValidationError(f"Ukuran foto maksimal {MAX_IMAGE_MB} MB.")
        return image


class LoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Nama pengguna atau kata sandi salah. Periksa lagi lalu coba masuk.",
        "inactive": "Akun ini dinonaktifkan. Hubungi pemilik kedai.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nama pengguna"
        self.fields["password"].label = "Kata sandi"
        self.fields["username"].widget.attrs.update(
            {"class": "input", "autocomplete": "username", "autofocus": True}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "input", "autocomplete": "current-password"}
        )
