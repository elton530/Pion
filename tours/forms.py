from django import forms


class TourReviewForm(forms.Form):
    rating = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        initial=5,
    )
    comment = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)


from django import forms
from .models import Tour, TourImage


class TourCreateForm(forms.ModelForm):
    class Meta:
        model = Tour
        fields = [
            "title",
            "description",
            "tour_type",
            "difficulty",
            "location_start",
            "duration_hours",
            "distance_km",
            "price_per_person",
            "max_participants",
            "date",
            "time_start",
            "main_image",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "date": forms.DateInput(attrs={"type": "date"}),
            "time_start": forms.TimeInput(attrs={"type": "time"}),
        }
