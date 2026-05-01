from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import GuideProfile, TouristProfile, TOUR_TYPES, EXPERIENCE_LEVELS


# ==================== USER REGISTRATION FORMS ====================

class SignupForm(UserCreationForm):
    """Forma për regjistrim të përdoruesit të ri"""
    
    ROLE_CHOICES = [
        ("tourist", "🧗 Jam Tourist (kërkoj ture)"),
        ("guide", "🏔️ Jam Guide Lokal (dua të ofroj ture)"),
    ]
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Emri juaj',
            }
        ),
        label="Emri"
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Mbiemri juaj',
            }
        ),
        label="Mbiemri"
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com',
            }
        ),
        label="Email"
    )
    
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Emri përdorues (username)',
                'help_text': 'Deri 150 karaktere. Vetëm numra, shkronja dhe @/./+/-/_',
            }
        ),
        label="Emri përdorues"
    )
    
    password1 = forms.CharField(
        label="Fjalëkalimi",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Fjalëkalimi (minimum 8 karaktere)',
            }
        ),
        help_text="Minimum 8 karaktere, jo vetëm numra"
    )
    
    password2 = forms.CharField(
        label="Konfirmo fjalëkalimin",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Përsërit fjalëkalimin',
            }
        )
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Zgjedh rolin tënd",
        help_text="Mund ta ndryshosh këtë më vonë"
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
        )
    
    def clean_email(self):
        """Kontrollo nëse email ekziston"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                _("Ky email ekziston tashmë. Provo email tjetër ose hyr në llogarinë tuaj.")
            )
        return email
    
    def clean_username(self):
        """Kontrollo nëse username ekziston"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError(
                _("Ky username ekziston tashmë. Zgjedh username tjetër.")
            )
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        
        if commit:
            user.save()
            
            # Krijo profile bazuar në rolin
            role = self.cleaned_data.get('role')
            if role == 'guide':
                GuideProfile.objects.get_or_create(user=user)
            elif role == 'tourist':
                TouristProfile.objects.get_or_create(user=user)
        
        return user


class UserAuthenticationForm(forms.Form):
    """Forma e thjeshtë për login"""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Username ose email',
                'autofocus': True,
            }
        ),
        label="Username ose Email"
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Fjalëkalimi',
            }
        ),
        label="Fjalëkalimi"
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Mbaj mua të lidhur"
    )
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

# ==================== GUIDE PROFILE FORMS ====================

class GuideProfileForm(forms.ModelForm):
    """Forma për krijimin e profilit të guide-it"""
    
    class Meta:
        model = GuideProfile
        fields = [
            'photo', 'bio', 'phone', 'location', 'languages',
            'specialty', 'specialties', 'experience_level', 'years_experience',
            'certifications', 'website', 'instagram', 'facebook'
        ]
        widgets = {
            'photo': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/*',
                }
            ),
            'bio': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Përshkrim personal (rreth teje, përvojës, pasionit për natyrën, etj.)',
                    'maxlength': '1000',
                }
            ),
            'phone': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'p.sh. +355 69 1234567',
                    'type': 'tel',
                }
            ),
            'location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'p.sh. Theth, Valbonë, Tiranë, Durrës',
                }
            ),
            'languages': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'p.sh. Shqip, Anglisht, Italisht, Gjermansht (të ndara me presje)',
                }
            ),
            'specialty': forms.Select(attrs={'class': 'form-select'}),
            'specialties': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Llojet e tureve që ofron (të ndara me presje)',
                }
            ),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'years_experience': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'placeholder': 'Numri i viteve',
                }
            ),
            'certifications': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Certifikime (ndihmë e parë, alpinizëm, guidë turistike, etj. - një për rresht)',
                }
            ),
            'website': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://example.com',
                }
            ),
            'instagram': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '@username_tuaj',
                }
            ),
            'facebook': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'facebook.com/profili_juaj',
                }
            ),
        }
        labels = {
            'photo': 'Foto profilit',
            'bio': 'Përshkrimi i shkurtër (bio)',
            'phone': 'Numri i telefonit',
            'location': 'Zona kryesore ku operon',
            'languages': 'Gjuhët që flet',
            'specialty': 'Specialiteti kryesor',
            'specialties': 'Llojet e tureve',
            'experience_level': 'Niveli i përvojës',
            'years_experience': 'Vitet e përvojës',
            'certifications': 'Certifikime',
            'website': 'Faqja juaj personale',
            'instagram': 'Instagram',
            'facebook': 'Facebook',
        }


class GuideEditProfileForm(forms.ModelForm):
    """Forma për redaktimin e profilit të guide-it (më e plotë)"""
    
    class Meta:
        model = GuideProfile
        fields = [
            'photo', 'bio', 'phone', 'location', 'languages',
            'specialty', 'specialties', 'experience_level', 'years_experience',
            'certifications', 'certification_document', 'website',
            'instagram', 'facebook', 'is_active'
        ]
        widgets = {
            'photo': forms.FileInput(
                attrs={'class': 'form-control', 'accept': 'image/*'}
            ),
            'bio': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 5}
            ),
            'phone': forms.TextInput(
                attrs={'class': 'form-control', 'type': 'tel'}
            ),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'languages': forms.TextInput(attrs={'class': 'form-control'}),
            'specialty': forms.Select(attrs={'class': 'form-select'}),
            'specialties': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'years_experience': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0'}
            ),
            'certifications': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4}
            ),
            'certification_document': forms.FileInput(
                attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}
            ),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control'}),
            'facebook': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ==================== TOURIST PROFILE FORMS ====================

class TouristProfileForm(forms.ModelForm):
    """Forma për krijimin e profilit të turistit"""
    
    class Meta:
        model = TouristProfile
        fields = [
            'photo', 'bio', 'phone', 'date_of_birth', 'country',
            'experience_level', 'preferred_tour_types', 'languages',
            'emergency_contact_name', 'emergency_contact_phone',
            'email_notifications', 'sms_notifications', 'newsletter'
        ]
        widgets = {
            'photo': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/*',
                }
            ),
            'bio': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Rreth teje dhe interesave tuaja',
                    'maxlength': '500',
                }
            ),
            'phone': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'p.sh. +355 69 1234567',
                    'type': 'tel',
                }
            ),
            'date_of_birth': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                }
            ),
            'country': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Vendi i origjinës',
                }
            ),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'preferred_tour_types': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'p.sh. Hiking, Alpine, Cycling (të ndara me presje)',
                }
            ),
            'languages': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'p.sh. Shqip, Anglisht, Italisht',
                }
            ),
            'emergency_contact_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Emri i kontaktit',
                }
            ),
            'emergency_contact_phone': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Numri i telefonit',
                    'type': 'tel',
                }
            ),
            'email_notifications': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'sms_notifications': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'newsletter': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
        labels = {
            'photo': 'Foto profilit',
            'bio': 'Përshkrimi i shkurtër',
            'phone': 'Numri i telefonit',
            'date_of_birth': 'Data e lindjes',
            'country': 'Vendi',
            'experience_level': 'Niveli i përvojës në outdoor',
            'preferred_tour_types': 'Llojet e tureve të preferuar',
            'languages': 'Gjuhët',
            'emergency_contact_name': 'Emri i kontaktit në emergjencë',
            'emergency_contact_phone': 'Numri i kontaktit në emergjencë',
            'email_notifications': 'Prij njoftimime përmes email-it',
            'sms_notifications': 'Prij njoftimime përmes SMS',
            'newsletter': 'Pajtohesh në newsletter',
        }


class TouristEditProfileForm(forms.ModelForm):
    """Forma për redaktimin e profilit të turistit"""
    
    class Meta:
        model = TouristProfile
        fields = [
            'photo', 'bio', 'phone', 'date_of_birth', 'country',
            'experience_level', 'preferred_tour_types', 'languages',
            'emergency_contact_name', 'emergency_contact_phone',
            'health_conditions', 'allergies',
            'email_notifications', 'sms_notifications', 'newsletter'
        ]
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'preferred_tour_types': forms.TextInput(attrs={'class': 'form-control'}),
            'languages': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(
                attrs={'class': 'form-control', 'type': 'tel'}
            ),
            'health_conditions': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'allergies': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'newsletter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ==================== PASSWORD FORMS ====================

class CustomPasswordChangeForm(PasswordChangeForm):
    """Forma për ndryshimin e fjalëkalimit"""
    
    old_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Fjalëkalimi i vjetër',
            }
        ),
        label="Fjalëkalimi i vjetër"
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Fjalëkalimi i ri',
            }
        ),
        label="Fjalëkalimi i ri"
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Përsërit fjalëkalimin e ri',
            }
        ),
        label="Konfirmo fjalëkalimin e ri"
    )