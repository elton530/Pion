from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import GuideProfile, TouristProfile


class SignupForm(UserCreationForm):
    ROLE_CHOICES = [
        ("tourist", "Jam Tourist (kërkoj ture)"),
        ("guide", "Jam Guide Lokal (dua të ofroj ture)"),
    ]

    first_name = forms.CharField(max_length=30, required=True, label="Emri")
    last_name = forms.CharField(max_length=30, required=True, label="Mbiemri")
    email = forms.EmailField(required=True, label="Email")
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, widget=forms.RadioSelect, label="Zgjedh rolin tënd"
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "role",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class GuideProfileForm(forms.ModelForm):
    class Meta:
        model = GuideProfile
        fields = [
            "photo",
            "bio",
            "phone",
            "location",
            "languages",
            "certifications",
            "specialty",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
            "certifications": forms.Textarea(attrs={"rows": 4}),
            "languages": forms.TextInput(
                attrs={"placeholder": "p.sh. Shqip, Anglisht, Italisht, Gjermanisht"}
            ),
            "location": forms.TextInput(
                attrs={"placeholder": "p.sh. Theth, Valbonë, Tiranë, Durrës"}
            ),
        }
        labels = {
            "photo": "Foto profilit",
            "bio": "Përshkrimi i shkurtër (bio)",
            "phone": "Numri i telefonit (me kod vendi, p.sh. +355...)",
            "location": "Zona kryesore ku operon",
            "languages": "Gjuhët që flet",
            "certifications": "Certifikime (ndihmë e parë, alpinizëm, guidë turistike etj.)",
            "specialty": "Specialiteti kryesor",
        }
