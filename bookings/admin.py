from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "tour",
        "tourist",
        "num_people",
        "total_price",
        "status",
        "created_at",
    ]
    list_filter = ["status", "tour__date", "tour__guide"]
    search_fields = [
        "tour__title",
        "tourist__user__first_name",
        "tourist__user__last_name",
    ]
    readonly_fields = ["total_price", "created_at"]
    actions = ["confirm_bookings", "cancel_bookings"]

    def confirm_bookings(self, request, queryset):
        queryset.update(status="confirmed")

    confirm_bookings.short_description = "Konfirmo rezervimet e zgjedhura"

    def cancel_bookings(self, request, queryset):
        for booking in queryset:
            booking.cancel()

    cancel_bookings.short_description = "Anullo dhe kthe vendet"
