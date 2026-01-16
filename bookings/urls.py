from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    path("tour/<slug:slug>/reserve/", views.create_booking, name="create_booking"),
    path("tour/<slug:slug>/success/", views.booking_success, name="booking_success"),
]
