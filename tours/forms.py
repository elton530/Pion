from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    Tour, TourImage, TourReview, TourSchedule, 
    TourFAQ, TOUR_TYPES,
    DIFFICULTY_LEVELS, AGE_GROUP_CHOICES
)


# ==================== HELPER WIDGETS ====================

class ControlInput(forms.TextInput):
    """Base widget për input me class form-control"""
    def __init__(self, attrs=None, **kwargs):
        default_attrs = {'class': 'form-control'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, **kwargs)


class ControlSelect(forms.Select):
    """Base widget për select me class form-select"""
    def __init__(self, attrs=None, **kwargs):
        default_attrs = {'class': 'form-select'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, **kwargs)


class ControlTextarea(forms.Textarea):
    """Base widget për textarea me class form-control"""
    def __init__(self, attrs=None, **kwargs):
        default_attrs = {'class': 'form-control'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, **kwargs)



# ==================== TOUR REVIEW FORMS ====================

class TourReviewForm(forms.ModelForm):
    """Forma për vlerësimet dhe komentet e turistëve"""
    
    class Meta:
        model = TourReview
        fields = ['rating', 'title', 'comment', 'guide_rating', 'value_rating', 'experience_rating']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, f"{i} ⭐") for i in range(1, 6)],
                attrs={'class': 'rating-radio'}
            ),
            'title': ControlInput(
                attrs={
                    'placeholder': 'Titulli i review-it (opsionale)',
                    'maxlength': '200'
                }
            ),
            'comment': ControlTextarea(
                attrs={
                    'rows': 5,
                    'placeholder': 'Ndja përvojën tuaj me turist të tjerë...',
                    'maxlength': '2000'
                }
            ),
            'guide_rating': forms.RadioSelect(
                choices=[(i, f"{i}") for i in range(1, 6)],
                attrs={'class': 'rating-radio small'}
            ),
            'value_rating': forms.RadioSelect(
                choices=[(i, f"{i}") for i in range(1, 6)],
                attrs={'class': 'rating-radio small'}
            ),
            'experience_rating': forms.RadioSelect(
                choices=[(i, f"{i}") for i in range(1, 6)],
                attrs={'class': 'rating-radio small'}
            ),
        }
        labels = {
            'rating': 'Vlerësimi përgjithësues',
            'title': 'Titulli',
            'comment': 'Komentimi juaj',
            'guide_rating': 'Vlerësimi i udhëzuesit',
            'value_rating': 'Vlerë për para',
            'experience_rating': 'Përvojë përgjithësisht',
        }
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '')
        if len(comment) < 10 and comment:
            raise forms.ValidationError(
                _("Komentimi duhet të ketë të paktën 10 karaktere.")
            )
        return comment


# ==================== TOUR IMAGE FORMS ====================

class TourImageForm(forms.ModelForm):
    """Forma për imazhet shtesë të turit"""
    
    class Meta:
        model = TourImage
        fields = ['image', 'caption', 'order', 'is_primary']
        widgets = {
            'image': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/*'
                }
            ),
            'caption': ControlInput(
                attrs={
                    'placeholder': 'Përshkrimi i imazhit (opsionale)',
                    'maxlength': '200'
                }
            ),
            'order': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'placeholder': 'Rendi i shfaqjes'
                }
            ),
            'is_primary': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
        labels = {
            'image': 'Imazhi',
            'caption': 'Përshkrimi',
            'order': 'Rendi',
            'is_primary': 'Vendose si foto kryesore',
        }


class TourImageFormSet(forms.BaseInlineFormSet):
    """FormSet për imazhet e turit"""
    
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        
        # Siguro që të paktën një imazh të jetë i markuar si primary
        primary_count = sum(
            1 for form in self.forms 
            if form.cleaned_data.get('is_primary') and not form.cleaned_data.get('DELETE')
        )
        
        if primary_count == 0 and any(
            form.cleaned_data.get('image') and not form.cleaned_data.get('DELETE')
            for form in self.forms
        ):
            raise forms.ValidationError(
                _("Duhet të përzgjedhësh të paktën një imazh si foto kryesore.")
            )


# ==================== TOUR CREATION FORM ====================

class TourCreateForm(forms.ModelForm):
    """Forma për krijimin e një turi (forma themelore)"""
    
    class Meta:
        model = Tour
        fields = [
            'title', 'short_description', 'full_description',
            'tour_type', 'difficulty', 'age_group',
            'meeting_point', 'location_city', 'location_region',
            'duration_hours', 'duration_days', 'distance_km',
            'price_per_person', 'currency', 'max_participants', 'min_participants',
            'date', 'time_start', 'time_end',
            'main_image', 'elevation_gain', 'max_altitude'
        ]
        widgets = {
            'title': ControlInput(
                attrs={
                    'class': 'form-control-lg',
                    'placeholder': 'P.sh. Ecje në Theth - Liqeni i Komanin',
                    'maxlength': '200'
                }
            ),
            'short_description': ControlTextarea(
                attrs={
                    'rows': 2,
                    'placeholder': 'Përshkrim i shkurtër (deri 300 karaktere)',
                    'maxlength': '300'
                }
            ),
            'full_description': ControlTextarea(
                attrs={
                    'rows': 8,
                    'placeholder': 'Përshkrim i detajuar: itinerari, aktivitetet, pemandja, etj.',
                }
            ),
            'tour_type': ControlSelect(),
            'difficulty': ControlSelect(),
            'age_group': ControlSelect(),
            'meeting_point': ControlInput(
                attrs={'placeholder': 'P.sh. Para Hyqes së Universitetit të Tiranës'}
            ),
            'location_city': ControlInput(
                attrs={'placeholder': 'Qyteti (Tiranë, Shkodër, etj.)'}
            ),
            'location_region': ControlInput(
                attrs={'placeholder': 'Rajoni (Dajti, Theth, Mali i Korab, etj.)'}
            ),
            'duration_hours': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Orë'}
            ),
            'duration_days': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Ditë (për turet shumë-ditore)'}
            ),
            'distance_km': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Km', 'type': 'number'}
            ),
            'elevation_gain': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Metra (opsionale)'}
            ),
            'max_altitude': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Metra (opsionale)'}
            ),
            'price_per_person': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00', 'type': 'number'}
            ),
            'currency': ControlSelect(),
            'max_participants': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'max': '100'}
            ),
            'min_participants': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'max': '50'}
            ),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'time_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'main_image': forms.FileInput(
                attrs={'class': 'form-control', 'accept': 'image/*', 'required': 'true'}
            ),
        }
        labels = {
            'title': 'Titulli i Turit',
            'short_description': 'Përshkrim i Shkurtër',
            'full_description': 'Përshkrim i Plotë',
            'tour_type': 'Lloji i Turit',
            'difficulty': 'Niveli i Vështirësisë',
            'age_group': 'Grupi Moshor',
            'meeting_point': 'Pika e Takimit',
            'location_city': 'Qyteti',
            'location_region': 'Rajoni',
            'duration_hours': 'Kohëzgjatja (Orë)',
            'duration_days': 'Kohëzgjatja (Ditë)',
            'distance_km': 'Distanca',
            'elevation_gain': 'Ngritja',
            'max_altitude': 'Lartësia Maksimale',
            'price_per_person': 'Çmimi për Person',
            'currency': 'Valuta',
            'max_participants': 'Maksimumi i Pjesëmarrësve',
            'min_participants': 'Minimumi i Pjesëmarrësve',
            'date': 'Data',
            'time_start': 'Ora e Nisjes',
            'time_end': 'Ora e Përfundimit',
            'main_image': 'Foto Kryesore',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time_start = cleaned_data.get('time_start')
        time_end = cleaned_data.get('time_end')
        
        # Kontrollo nëse data është në të ardhmen
        if date and date < timezone.now().date():
            raise forms.ValidationError(
                _("Data e turit duhet të jetë në të ardhmen.")
            )
        
        # Kontrollo kohën e përfundimit
        if time_end and time_start and time_end <= time_start:
            raise forms.ValidationError(
                _("Ora e përfundimit duhet të jetë më vonë se ora e nisjes.")
            )
        
        # Kontrollo kapacitetin
        min_part = cleaned_data.get('min_participants')
        max_part = cleaned_data.get('max_participants')
        
        if min_part and max_part and min_part > max_part:
            raise forms.ValidationError(
                _("Minimumi i pjesëmarrësve nuk mund të jetë më i madh se maksimumi.")
            )
        
        return cleaned_data


# ==================== TOUR EDIT FORM ====================

class TourEditForm(forms.ModelForm):
    """Forma për redaktimin e një turi (forma e plotë)"""
    
    class Meta:
        model = Tour
        fields = [
            'title', 'slug', 'short_description', 'full_description',
            'tour_type', 'difficulty', 'age_group', 'languages',
            'meeting_point', 'meeting_point_lat', 'meeting_point_lng',
            'location_city', 'location_region', 'end_point',
            'duration_hours', 'duration_days', 'distance_km',
            'elevation_gain', 'max_altitude',
            'price_per_person', 'currency',
            'max_participants', 'min_participants',
            'date', 'time_start', 'time_end',
            'main_image', 'thumbnail',
            'highlights', 'included', 'not_included', 'what_to_bring',
            'requirements', 'health_warnings', 'equipment_provided',
            'transportation_included', 'transportation_details',
            'meal_included', 'meal_details',
            'accommodation_included', 'accommodation_details',
            'cancellation_deadline_hours', 'refund_percentage',
            'status'
        ]
        widgets = {
            'title': ControlInput(attrs={'class': 'form-control-lg'}),
            'slug': ControlInput(attrs={'readonly': 'readonly'}),
            'short_description': ControlTextarea(attrs={'rows': 2}),
            'full_description': ControlTextarea(attrs={'rows': 8}),
            'tour_type': ControlSelect(),
            'difficulty': ControlSelect(),
            'age_group': ControlSelect(),
            'languages': ControlSelect(),
            'meeting_point': ControlInput(),
            'meeting_point_lat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'meeting_point_lng': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'location_city': ControlInput(),
            'location_region': ControlInput(),
            'end_point': ControlInput(),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'distance_km': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'type': 'number'}),
            'elevation_gain': forms.NumberInput(attrs={'class': 'form-control', 'type': 'number'}),
            'max_altitude': forms.NumberInput(attrs={'class': 'form-control', 'type': 'number'}),
            'price_per_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'type': 'number'}),
            'currency': ControlSelect(),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '100'}),
            'min_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'time_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'main_image': forms.FileInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'highlights': ControlTextarea(attrs={'rows': 4, 'placeholder': 'Një për rresht'}),
            'included': ControlTextarea(attrs={'rows': 4, 'placeholder': 'Një për rresht'}),
            'not_included': ControlTextarea(attrs={'rows': 4, 'placeholder': 'Një për rresht'}),
            'what_to_bring': ControlTextarea(attrs={'rows': 4, 'placeholder': 'Një për rresht'}),
            'requirements': ControlTextarea(attrs={'rows': 3}),
            'health_warnings': ControlTextarea(attrs={'rows': 3}),
            'equipment_provided': ControlTextarea(attrs={'rows': 3}),
            'transportation_included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'transportation_details': ControlTextarea(attrs={'rows': 3}),
            'meal_included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meal_details': ControlTextarea(attrs={'rows': 3}),
            'accommodation_included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accommodation_details': ControlTextarea(attrs={'rows': 3}),
            'cancellation_deadline_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'refund_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'status': ControlSelect(),
        }


# ==================== TOUR PRICING FORM ====================

class TourPricingForm(forms.ModelForm):
    """Forma për çmimet dhe zbritjet"""
    
    class Meta:
        model = Tour
        fields = [
            'price_per_person', 'currency', 'max_participants', 'min_participants',
            'has_discount', 'discount_price', 'discount_until',
            'early_bird_days', 'early_bird_discount'
        ]
        widgets = {
            'price_per_person': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'type': 'number'}
            ),
            'currency': ControlSelect(),
            'max_participants': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'max': '100', 'type': 'number'}
            ),
            'min_participants': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1', 'type': 'number'}
            ),
            'has_discount': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'discount_price': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'type': 'number'}
            ),
            'discount_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'early_bird_days': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Ditë para turit', 'type': 'number'}
            ),
            'early_bird_discount': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': 'Përqindje', 'type': 'number'}
            ),
        }
        labels = {
            'price_per_person': 'Çmimi për Person',
            'currency': 'Valuta',
            'max_participants': 'Maksimumi i Pjesëmarrësve',
            'min_participants': 'Minimumi i Pjesëmarrësve',
            'has_discount': 'Zbritja Aktuale?',
            'discount_price': 'Çmimi me Zbritje',
            'discount_until': 'Zbritja Deri:',
            'early_bird_days': 'Ditë për Early Bird',
            'early_bird_discount': 'Përqindja Early Bird',
        }


# ==================== TOUR SCHEDULE FORM ====================

class TourScheduleForm(forms.ModelForm):
    """Forma për programin ditor të turit"""
    
    class Meta:
        model = TourSchedule
        fields = ['day_number', 'title', 'description', 'start_time', 'end_time', 'meals_included', 'accommodation', 'order']
        widgets = {
            'day_number': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'P.sh. Në qendrën e mallit'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'meals_included': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'P.sh. Mëngjes, Dreka, Darka'}
            ),
            'accommodation': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


# ==================== TOUR FAQ FORM ====================

class TourFAQForm(forms.ModelForm):
    """Forma për pyetje të shpeshta"""
    
    class Meta:
        model = TourFAQ
        fields = ['question', 'answer', 'order', 'is_active']
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pyetja'}),
            'answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Përgjigja'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ==================== TOUR SEARCH AND FILTER FORM ====================

class TourSearchForm(forms.Form):
    """Forma për kërkimin dhe filtrimin e tureve"""
    
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=ControlInput(attrs={'placeholder': 'Kërko tur, lokacion, ...'}),
        label='Kërkim'
    )
    
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=ControlInput(attrs={'placeholder': 'Qyteti ose rajoni'}),
        label='Lokacioni'
    )
    
    tour_type = forms.MultipleChoiceField(
        choices=TOUR_TYPES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Lloji i Turit'
    )
    
    difficulty = forms.MultipleChoiceField(
        choices=DIFFICULTY_LEVELS,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Vështirësia'
    )
    
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'type': 'number', 'step': '0.01', 'placeholder': 'Min'}
        ),
        label='Çmim Min'
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'type': 'number', 'step': '0.01', 'placeholder': 'Max'}
        ),
        label='Çmim Max'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Nga Data'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Deri Data'
    )
    
    age_group = forms.ChoiceField(
        choices=[('', '-- Zgjedh Grupin Moshor --')] + list(AGE_GROUP_CHOICES),
        required=False,
        widget=ControlSelect(),
        label='Grupi Moshor'
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('-date', 'Më të ardhshmi'),
            ('price_per_person', 'Çmimi: Më të Lirë'),
            ('-price_per_person', 'Çmimi: Më të Shtrenjtë'),
            ('-average_rating', 'Vlerësimi: Më të Mirë'),
            ('-created_at', 'Më të Rinj'),
        ],
        required=False,
        widget=ControlSelect(),
        label='Renditi'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price and max_price and min_price > max_price:
            raise forms.ValidationError(
                _("Çmimi minimal nuk mund të jetë më i madh se çmimi maksimal.")
            )
        
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(
                _("Data fillestare nuk mund të jetë më pas datës përfundimtare.")
            )
        
        return cleaned_data