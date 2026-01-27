from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import ContactMessage, NewsletterSubscription


# ==================== CONTACT FORM ====================

class ContactForm(forms.ModelForm):
    """Forma për kontaktin"""
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'placeholder': 'Emri juaj i plotë',
                    'maxlength': '100',
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'placeholder': 'email@example.com',
                    'type': 'email',
                }
            ),
            'phone': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '+355 69 1234567',
                    'type': 'tel',
                }
            ),
            'subject': forms.TextInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'placeholder': 'Tema e mesazhit',
                    'maxlength': '200',
                }
            ),
            'message': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 6,
                    'placeholder': 'Shkruaj mesazhin tuaj këtu...',
                    'maxlength': '5000',
                }
            ),
        }
        labels = {
            'name': 'Emri *',
            'email': 'Email *',
            'phone': 'Telefon (opsionale)',
            'subject': 'Tema *',
            'message': 'Mesazhi *',
        }
    
    def clean_name(self):
        """Valido emrin"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError(_("Emri është i detyrueshëm."))
        
        if len(name) < 2:
            raise ValidationError(_("Emri duhet të ketë të paktën 2 karaktere."))
        
        if len(name) > 100:
            raise ValidationError(_("Emri është shumë i gjatë."))
        
        return name
    
    def clean_email(self):
        """Valido email-in"""
        email = self.cleaned_data.get('email', '').strip()
        
        if not email:
            raise ValidationError(_("Email-i është i detyrueshëm."))
        
        return email
    
    def clean_subject(self):
        """Valido temën"""
        subject = self.cleaned_data.get('subject', '').strip()
        
        if not subject:
            raise ValidationError(_("Tema është e detyrueshme."))
        
        if len(subject) < 5:
            raise ValidationError(_("Tema duhet të ketë të paktën 5 karaktere."))
        
        return subject
    
    def clean_message(self):
        """Valido mesazhin"""
        message = self.cleaned_data.get('message', '').strip()
        
        if not message:
            raise ValidationError(_("Mesazhi është i detyrueshëm."))
        
        if len(message) < 10:
            raise ValidationError(_("Mesazhi duhet të ketë të paktën 10 karaktere."))
        
        if len(message) > 5000:
            raise ValidationError(_("Mesazhi është shumë i gjatë."))
        
        return message
    
    def clean(self):
        """Validim përgjithësues"""
        cleaned_data = super().clean()
        
        # Kontrollo spam patterns
        message = cleaned_data.get('message', '').lower()
        spam_keywords = ['viagra', 'casino', 'lottery', 'bitcoin']
        
        if any(keyword in message for keyword in spam_keywords):
            raise ValidationError(
                _("Mesazhi juaj përmban përkatësi të dyshimta. Ju lutemi provoni më vonë.")
            )
        
        return cleaned_data


class ContactFormAnonymous(ContactForm):
    """Forma kontakti për përdoruesit e paloguar"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bëj të detyrueshëm emailin dhe telefonin për përdoruesit e paloguar
        self.fields['email'].required = True
        self.fields['phone'].required = True


class ContactFormAuthenticated(ContactForm):
    """Forma kontakti për përdoruesit e loguar"""
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if user and user.is_authenticated:
            # Plotëso emrin dhe email-in automatikisht
            self.fields['name'].initial = user.get_full_name() or user.username
            self.fields['email'].initial = user.email
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['email'].widget.attrs['readonly'] = True


# ==================== NEWSLETTER FORM ====================

class NewsletterSubscriptionForm(forms.ModelForm):
    """Forma për nënshkrim newsletter"""
    
    class Meta:
        model = NewsletterSubscription
        fields = ['email', 'name']
        widgets = {
            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'email@example.com',
                    'type': 'email',
                    'required': True,
                }
            ),
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Emri juaj (opsionale)',
                    'maxlength': '100',
                }
            ),
        }
        labels = {
            'email': 'Email *',
            'name': 'Emri (opsionale)',
        }
    
    agree_privacy = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("Pajtohem me politikën e privatësisë"),
        help_text=_("Ne nuk do të ndajmë email-in tuaj.")
    )
    
    def clean_email(self):
        """Valido email-in"""
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if not email:
            raise ValidationError(_("Email-i është i detyrueshëm."))
        
        # Kontrollo nëse ekziston tashmë
        if NewsletterSubscription.objects.filter(email=email).exists():
            raise ValidationError(
                _("Ky email është tashmë i nënshkruar në newsletter-in tonë.")
            )
        
        return email
    
    def clean_name(self):
        """Valido emrin"""
        name = self.cleaned_data.get('name', '').strip()
        
        if name and len(name) < 2:
            raise ValidationError(_("Emri duhet të ketë të paktën 2 karaktere."))
        
        return name


class NewsletterUnsubscribeForm(forms.Form):
    """Forma për anulimin e nënshkrimit"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'email@example.com',
                'type': 'email',
            }
        ),
        label=_("Email *"),
        help_text=_("Futni email-in për të anulluar nënshkrimin")
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("Konfirmoj anulimin e nënshkrimit"),
        help_text=_("Ky veprim nuk mund të zhbëhet")
    )
    
    def clean_email(self):
        """Valido email-in"""
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if not email:
            raise ValidationError(_("Email-i është i detyrueshëm."))
        
        # Kontrollo nëse ekziston
        try:
            NewsletterSubscription.objects.get(email=email, is_active=True)
        except NewsletterSubscription.DoesNotExist:
            raise ValidationError(
                _("Ky email nuk është i nënshkruar në newsletter-in tonë.")
            )
        
        return email
    
    def clean_confirm(self):
        """Valido konfirmimin"""
        confirm = self.cleaned_data.get('confirm')
        
        if not confirm:
            raise ValidationError(_("Duhet të konfirmosh anulimin."))
        
        return confirm


# ==================== SEARCH FORM ====================

class GlobalSearchForm(forms.Form):
    """Forma për kërkimin global"""
    
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Kërko tur, guide, lokacion...',
                'autocomplete': 'off',
            }
        ),
        label=_("Kërkim")
    )
    
    search_type = forms.ChoiceField(
        choices=[
            ('all', 'Të gjitha'),
            ('tours', 'Turet'),
            ('guides', 'Guide-t'),
            ('locations', 'Lokacionet'),
        ],
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_("Lloji i kërkimit"),
        initial='all'
    )
    
    def clean_query(self):
        """Valido kërkimin"""
        query = self.cleaned_data.get('query', '').strip()
        
        if query and len(query) < 2:
            raise ValidationError(_("Kërkimi duhet të ketë të paktën 2 karaktere."))
        
        return query


# ==================== NEWSLETTER ADMIN FORM ====================

class BulkNewsletterForm(forms.Form):
    """Forma për dërgimin e bulk emails"""
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Tema e email-it',
            }
        ),
        label=_("Tema *")
    )
    
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Teksti i email-it',
            }
        ),
        label=_("Mesazhi *")
    )
    
    include_active_only = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("Vetëm nënshkruesit aktivë"),
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("Konfirmoj dërgimin e email-it te %(count)d nënshkruesit"),
    )
    
    def clean_subject(self):
        """Valido temën"""
        subject = self.cleaned_data.get('subject', '').strip()
        
        if not subject:
            raise ValidationError(_("Tema është e detyrueshme."))
        
        return subject
    
    def clean_message(self):
        """Valido mesazhin"""
        message = self.cleaned_data.get('message', '').strip()
        
        if not message:
            raise ValidationError(_("Mesazhi është i detyrueshëm."))
        
        if len(message) < 20:
            raise ValidationError(_("Mesazhi duhet të ketë të paktën 20 karaktere."))
        
        return message
    
    def clean_confirm(self):
        """Valido konfirmimin"""
        confirm = self.cleaned_data.get('confirm')
        
        if not confirm:
            raise ValidationError(_("Duhet të konfirmosh dërgimin."))
        
        return confirm


# ==================== FEEDBACK FORM ====================

class FeedbackForm(forms.Form):
    """Forma për feedback të shpejtë"""
    
    RATING_CHOICES = [
        (5, '⭐⭐⭐⭐⭐ Shumë i mirë'),
        (4, '⭐⭐⭐⭐ I mirë'),
        (3, '⭐⭐⭐ Mesatar'),
        (2, '⭐⭐ I dobët'),
        (1, '⭐ Shumë i dobët'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_("Si e vlerësoi përvojën?"),
    )
    
    comment = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Komenti juaj (opsionale)',
            }
        ),
        label=_("Komentimi"),
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com',
                'type': 'email',
            }
        ),
        label=_("Email (për të marrë përgjigje)"),
    )
    
    def clean_comment(self):
        """Valido komentin"""
        comment = self.cleaned_data.get('comment', '').strip()
        
        if comment and len(comment) < 5:
            raise ValidationError(_("Komentimi duhet të ketë të paktën 5 karaktere."))
        
        return comment