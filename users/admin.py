from django.contrib import admin
from .models import GuideProfile, TouristProfile


@admin.register(GuideProfile)
class GuideProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "location", "phone", "specialty"]
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "location",
    ]


@admin.register(TouristProfile)
class TouristProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone"]
    search_fields = ["user__username", "user__first_name", "user__last_name"]
