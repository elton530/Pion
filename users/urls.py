from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "users"

# Pattern: /users/...

urlpatterns = [
    # ==================== AUTHENTICATION ====================
    # GET/POST /users/signup/ - Regjistrim i ri
    path("signup/", views.signup, name="signup"),
    
    # GET/POST /users/login/ - Login
    path("login/", views.CustomLoginView.as_view(), name="login"),
    
    # GET /users/logout/ - Logout
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    
    
    # ==================== PASSWORD MANAGEMENT ====================
    # GET/POST /users/password-change/ - Ndryshim fjalëkalimi
    path(
        "password-change/",
        views.CustomPasswordChangeView.as_view(),
        name="password_change"
    ),
    
    # GET /users/password-change/done/ - Konfirmim ndryshimi
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="users/password_change_done.html"
        ),
        name="password_change_done"
    ),
    
    # GET /users/password-reset/ - Kërkesë për reset
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset.html",
            email_template_name="users/password_reset_email.html",
            success_url="/users/password-reset/done/"
        ),
        name="password_reset"
    ),
    
    # GET /users/password-reset/done/ - Konfirmim reset
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html"
        ),
        name="password_reset_done"
    ),
    
    # GET /users/reset/<uidb64>/<token>/ - Link i reset-it
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url="/users/reset/done/"
        ),
        name="password_reset_confirm"
    ),
    
    # GET /users/reset/done/ - Konfirmim përfundimit
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),
    
    
    # ==================== GUIDE ROUTES ====================
    # GET /users/guide/dashboard/ - Dashboard i guide-it
    path("guide/dashboard/", views.guide_dashboard, name="guide_dashboard"),
    
    # GET/POST /users/guide/profile/edit/ - Redaktim profili
    path("guide/profile/edit/", views.guide_profile_edit, name="guide_profile_edit"),
    
    # GET /users/guide/booking/<booking_id>/ - Detajet e booking-ut
        path(
            "guide/booking/<uuid:booking_id>/",
        views.guide_booking_detail,
        name="guide_booking_detail"
    ),
    
    # POST /users/guide/booking/<booking_id>/confirm/ - Konfirmim booking-ut
        path(
            "guide/booking/<uuid:booking_id>/confirm/",
        views.guide_booking_action,
        {"action": "confirm"},
        name="guide_booking_confirm"
    ),
    
    # POST /users/guide/booking/<booking_id>/cancel/ - Anulim booking-ut
        path(
            "guide/booking/<uuid:booking_id>/cancel/",
        views.guide_booking_action,
        {"action": "cancel"},
        name="guide_booking_cancel"
    ),
    
    
    # ==================== TOURIST ROUTES ====================
    # GET /users/tourist/dashboard/ - Dashboard i turistit
    path("tourist/dashboard/", views.tourist_dashboard, name="tourist_dashboard"),

    # GET /users/saved-tours/ - Ture të ruajtura
    path("saved-tours/", views.saved_tours, name="saved_tours"),

    # GET /users/history/ - Historiku
    path("history/", views.history, name="history"),
    
    # GET/POST /users/tourist/profile/edit/ - Redaktim profili
    path(
        "tourist/profile/edit/",
        views.tourist_profile_edit,
        name="tourist_profile_edit"
    ),
    
    # GET /users/tourist/booking/<booking_id>/ - Detajet e booking-ut
        path(
            "tourist/booking/<uuid:booking_id>/",
        views.tourist_booking_detail,
        name="tourist_booking_detail"
    ),
    
    # POST /users/tourist/booking/<booking_id>/confirm/ - Konfirmim pjesëmarrjeje (24h)
        path(
            "tourist/booking/<uuid:booking_id>/confirm/",
            views.tourist_confirm_participation,
            name="tourist_booking_confirm"
        ),
    
        # POST /users/tourist/booking/<booking_id>/cancel/ - Anulim booking-ut
        path(
            "tourist/booking/<uuid:booking_id>/cancel/",
            views.tourist_booking_cancel,
            name="tourist_booking_cancel"
        ),
    
    
    # ==================== PROFILE VIEWS ====================
    # GET /users/profile/@<username>/ - Profili publik i guide-it
    path(
        "profile/@<slug:username>/",
        views.UserProfileDetailView.as_view(),
        name="guide_profile_public"
    ),
]