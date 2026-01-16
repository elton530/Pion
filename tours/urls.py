from django.urls import path
from . import views
from .views import TourDetailView, TourListView

app_name = "tours"

urlpatterns = [
    path("create/", views.create_tour, name="create_tour"),
    path("", TourListView.as_view(), name="tour_list"),
    path("<slug:slug>/", TourDetailView.as_view(), name="tour_detail"),
    path("<slug:slug>/review/", views.create_review, name="create_review"),
]
