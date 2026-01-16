from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "users"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("guide/profile/edit/", views.guide_profile_edit, name="guide_profile_edit"),
    path("guide/dashboard/", views.guide_dashboard, name="guide_dashboard"),
    path(
        "guide/booking/<int:booking_id>/<str:action>/",
        views.booking_action,
        name="booking_action",
    ),
    path("tourist/dashboard/", views.tourist_dashboard, name="tourist_dashboard"),
    path(
        "tourist/booking/<int:booking_id>/confirm/",
        views.confirm_participation,
        name="confirm_participation",
    ),
    path(
        "tourist/booking/<int:booking_id>/cancel/",
        views.cancel_booking,
        name="cancel_booking",
    ),
    path(
        "login/",
        views.CustomLoginView.as_view(),
        name="login",
    ),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
]
