from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Booking, BookingReview, CANCELLATION_REASON


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
