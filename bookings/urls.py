from django.urls import path
from . import views

app_name = "bookings"

# Pattern: /bookings/...

urlpatterns = [
    # ==================== BOOKING CREATION ====================
    # POST /bookings/tour/<slug>/reserve/ - Krijo prenim
    path(
        "tour/<slug:slug>/reserve/",
        views.create_booking,
        name="create_booking"
    ),
    
    # GET /bookings/success/<booking_id>/ - Faqja e suksesit
    path(
        "success/<uuid:booking_id>/",
        views.booking_success,
        name="booking_success"
    ),
    
    
    # ==================== BOOKING MANAGEMENT ====================
    # GET /bookings/<booking_id>/ - Detajet e prenimit
    path(
        "<uuid:booking_id>/",
        views.booking_detail,
        name="booking_detail"
    ),
    
    # GET/POST /bookings/<booking_id>/edit/ - Redaktim prenimit
    path(
        "<uuid:booking_id>/edit/",
        views.booking_edit,
        name="booking_edit"
    ),
    
    # GET/POST /bookings/<booking_id>/cancel/ - Anulim prenimit
    path(
        "<uuid:booking_id>/cancel/",
        views.booking_cancel,
        name="booking_cancel"
    ),
    
    # POST /bookings/<booking_id>/confirm-participation/ - Konfirmim 24h
    path(
        "<uuid:booking_id>/confirm-participation/",
        views.booking_confirm_participation,
        name="booking_confirm_participation"
    ),
    
    
    # ==================== BOOKING LISTING ====================
    # GET /bookings/my-bookings/ - Lista e prenimeve të turistit
    path(
        "my-bookings/",
        views.booking_list,
        name="booking_list"
    ),
    
    
    # ==================== REVIEWS ====================
    # POST /bookings/<booking_id>/review/ - Krijo vlerësim
    path(
        "<uuid:booking_id>/review/",
        views.create_booking_review,
        name="create_booking_review"
    ),
]