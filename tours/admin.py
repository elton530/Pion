from django.contrib import admin
from .models import Tour, TourImage


class TourImageInline(admin.TabularInline):
    model = TourImage
    extra = 1


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "guide",
        "date",
        "tour_type",
        "price_per_person",
        "available_spots",
        "is_active",
    ]
    list_filter = ["tour_type", "difficulty", "date", "is_active"]
    search_fields = [
        "title",
        "description",
        "guide__user__first_name",
        "guide__user__last_name",
    ]
    inlines = [TourImageInline]
    prepopulated_fields = {"slug": ("title",)}
