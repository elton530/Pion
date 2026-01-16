from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["num_people", "notes"]
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "p.sh. Kam fëmijë të vegjël, a ka vështirësi?",
                }
            ),
        }
        labels = {
            "num_people": "Numri i personave (përfshirë ty)",
            "notes": "Shënime ose pyetje për guidën",
        }

    def __init__(self, *args, tour=None, tourist=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tour = tour
        self.tourist = tourist

        if tour:
            max_people = tour.available_spots
            self.fields["num_people"].widget = forms.NumberInput(
                attrs={"min": 1, "max": max_people}
            )
            self.fields["num_people"].help_text = (
                f"Maksimumi i lejuar: {max_people} vende të lira"
            )

    def clean_num_people(self):
        num = self.cleaned_data["num_people"]
        if self.tour and num > self.tour.available_spots:
            raise forms.ValidationError(
                f"Vetëm {self.tour.available_spots} vende të lira!"
            )
        return num
