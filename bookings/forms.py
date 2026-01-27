from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Booking, Payment, BookingReview, CANCELLATION_REASON


# ==================== BOOKING FORMS ====================

class BookingForm(forms.ModelForm):
    """Forma për krijimin e një prenimit të ri"""
    
    class Meta:
        model = Booking
        fields = ['num_people', 'special_requirements', 'notes']
        widgets = {
            'num_people': forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'min': '1',
                    'placeholder': 'Numri i personave',
                }
            ),
            'special_requirements': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'P.sh. Alergjitë ushqimore, mobilitet i kufizuar, fëmijë, etj.',
                    'maxlength': '500',
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Pyetje për guidën, kërkesa speciale, shënime shtesë',
                    'maxlength': '1000',
                }
            ),
        }
        labels = {
            'num_people': 'Numri i personave (përfshirë ty)',
            'special_requirements': 'Kërkesa speciale',
            'notes': 'Shënime ose pyetje për guidën',
        }
    
    def __init__(self, *args, tour=None, tourist=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tour = tour
        self.tourist = tourist
        
        if tour:
            max_people = tour.available_spots
            
            # Përditëso widget-in për num_people
            self.fields['num_people'].widget = forms.NumberInput(
                attrs={
                    'class': 'form-control form-control-lg',
                    'min': '1',
                    'max': max_people,
                    'placeholder': f'Max {max_people} persona',
                }
            )
            
            self.fields['num_people'].help_text = (
                f'📍 Vende të lira: <strong>{max_people}</strong>'
            )
            
            # Set initial value
            if not self.instance.pk:
                self.fields['num_people'].initial = 1
    
    def clean_num_people(self):
        """Valido numrin e personave"""
        num = self.cleaned_data.get('num_people')
        
        if not num:
            raise ValidationError(_("Numri i personave është i detyrueshëm."))
        
        if num < 1:
            raise ValidationError(_("Duhet të ketë të paktën 1 person."))
        
        if self.tour and num > self.tour.available_spots:
            raise ValidationError(
                _("Nuk ka vende të mjaftueshme. Vende të lira: %(spots)d"),
                code='not_enough_spots',
                params={'spots': self.tour.available_spots}
            )
        
        return num
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Kontrollo nëse turist dhe tur janë të vlefshme
        if self.tourist and self.tour:
            # Kontrollo nëse ka tashmë prenim për këtë turist+tur
            existing = Booking.objects.filter(
                tourist=self.tourist,
                tour=self.tour
            ).exclude(status='cancelled')
            
            if existing.exists() and not self.instance.pk:
                raise ValidationError(
                    _("Ti ke tashmë një prenim për këtë tur."),
                    code='booking_exists'
                )
        
        return cleaned_data


class BookingEditForm(forms.ModelForm):
    """Forma për redaktimin e një prenimit"""
    
    class Meta:
        model = Booking
        fields = ['num_people', 'special_requirements', 'notes']
        widgets = {
            'num_people': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'readonly': True}
            ),
            'special_requirements': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nuk mund ta ndryshosh numrin e personave pas krijimit
        self.fields['num_people'].disabled = True


class BookingCancellationForm(forms.Form):
    """Forma për anulimin e një prenimit"""
    
    cancellation_reason = forms.ChoiceField(
        choices=CANCELLATION_REASON,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Arsyeja e anulimit',
        help_text='Zgjedh arsyezen për anulimin'
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detaje shtesë (opsionale)',
                'maxlength': '500',
            }
        ),
        required=False,
        label='Detaje shtesë',
        max_length=500
    )
    
    confirm = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Konfirmoj anulimin e këtij prenimit',
        help_text='Ky veprim nuk mund të zhbëhet'
    )
    
    def clean_confirm(self):
        """Siguro konfirmimin"""
        confirm = self.cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError(_("Duhet të konfirmosh anulimin."))
        return confirm


class BookingConfirmationForm(forms.Form):
    """Forma për konfirmimin e pjesëmarrjes (24h përpara)"""
    
    confirm = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Konfirmoj se do të marr pjesë në këtë tur',
        help_text='Duke konfirmuar, zotohesh të jesh pranë në orën e planifikuar'
    )
    
    def clean_confirm(self):
        """Valido konfirmimin"""
        confirm = self.cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError(_("Duhet të konfirmosh pjesëmarrjen tuaj."))
        return confirm


# ==================== PAYMENT FORMS ====================

class PaymentForm(forms.ModelForm):
    """Forma për pagesa"""
    
    class Meta:
        model = Payment
        fields = ['payment_method', 'notes']
        widgets = {
            'payment_method': forms.RadioSelect(
                attrs={'class': 'form-check-input'}
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Shënime shtesë (opsionale)',
                }
            ),
        }
        labels = {
            'payment_method': 'Metoda e pagesës',
            'notes': 'Shënime',
        }
    
    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking
        
        if booking:
            self.fields['amount'].initial = booking.final_price
            self.fields['amount'].disabled = True


class PaymentMethodForm(forms.Form):
    """Zgjedhja e metodës së pagesës"""
    
    PAYMENT_METHODS = [
        ('card', '💳 Kartë krediti/debit'),
        ('paypal', '🅿️ PayPal'),
        ('bank_transfer', '🏦 Transferim bankare'),
        ('cash', '💵 Në vend'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Zgjedh metodën e pagesës'
    )
    
    agree_terms = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Pajtohem me kushtet dhe politikën e anulimit',
        help_text='Lexo kushtet përpara se të vazhdo'
    )
    
    def clean_agree_terms(self):
        """Valido pajtimin"""
        agree = self.cleaned_data.get('agree_terms')
        if not agree:
            raise ValidationError(_("Duhet të pajtohen me kushtet për të vazhduar."))
        return agree


# ==================== REVIEW FORMS ====================

class BookingReviewForm(forms.ModelForm):
    """Forma për vlerësimin e prenimit"""
    
    class Meta:
        model = BookingReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, f"{i} ⭐") for i in range(1, 6)],
                attrs={'class': 'form-check-input'}
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Ndaj përvojën tuaj me udhëzuesin dhe turet të tjerë...',
                    'maxlength': '1000',
                }
            ),
        }
        labels = {
            'rating': 'Vlerësim',
            'comment': 'Komentari juaj',
        }
    
    def clean_comment(self):
        """Valido komentin"""
        comment = self.cleaned_data.get('comment', '')
        
        if len(comment) < 10 and comment:
            raise ValidationError(
                _("Komentimi duhet të ketë të paktën 10 karaktere.")
            )
        
        return comment


# ==================== ADMIN FORMS ====================

class GuideBookingManagementForm(forms.Form):
    """Forma për menaxhimin e prenimeve nga guide-i"""
    
    ACTION_CHOICES = [
        ('confirm', '✅ Konfirmoje'),
        ('cancel', '❌ Anuloje'),
        ('mark_completed', '✔️ Marko si të përfunduar'),
        ('mark_no_show', '⚠️ Marko si nuk u paraqit'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Zgjidh veprimin'
    )
    
    guide_notes = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Shënime për turisti (opsionale)',
            }
        ),
        required=False,
        label='Shënime',
        max_length=500
    )
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        
        if not action:
            raise ValidationError(_("Zgjidh një veprim."))
        
        return cleaned_data


# ==================== SEARCH & FILTER FORMS ====================

class BookingSearchForm(forms.Form):
    """Forma për kërkimin e prenimeve"""
    
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Kërko sipas turit, turistit, etj.',
            }
        ),
        label='Kërkim'
    )
    
    status = forms.MultipleChoiceField(
        choices=[('', '-- Të gjitha statuset --')] + list(
            [(s[0], s[1]) for s in [
                ('pending', 'Në pritje'),
                ('confirmed', 'Konfirmuar'),
                ('completed', 'Përfunduar'),
                ('cancelled', 'Anulluar'),
            ]]
        ),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Statusi'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date',
            }
        ),
        label='Nga data'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date',
            }
        ),
        label='Deri data'
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Më të rijet'),
            ('created_at', 'Më të vjetret'),
            ('-updated_at', 'Përditësime të fundit'),
            ('final_price', 'Çmim: më i lirë'),
            ('-final_price', 'Çmim: më i shtrenjtë'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Renditi'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                _("Data fillestare nuk mund të jetë më pas datës përfundimtare.")
            )
        
        return cleaned_data