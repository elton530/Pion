from django.urls import path
from . import views
from .views import (
    TourDetailView, TourListView, TourSearchView
)
from . import status_views

app_name = "tours"

# Pattern: /tours/...

urlpatterns = [
    # ==================== TOUR LISTING & SEARCHING ====================
    # GET /tours/ - Lista e tureve me filtrimin
    path("", TourListView.as_view(), name="tour_list"),
    
    # GET /tours/search/ - Kërkimi i avancuar
    path("search/", TourSearchView.as_view(), name="tour_search"),
    
    # GET /tours/featured/ - Turet featured
    path("featured/", views.featured_tours, name="featured_tours"),
    
    # GET /tours/location/<location>/ - Turet sipas lokacionit
    path("location/<str:location>/", views.tour_by_location, name="tour_by_location"),
    
    
    # ==================== GUIDE'S TOURS ====================
    # GET /tours/my-tours/ - Lista e tureve të guide-it
    path("my-tours/", views.my_tours, name="my_tours"),
    
    # POST /tours/create/ - Krijimi i turit të ri
    path("create/", views.create_tour, name="create_tour"),
    
    
    # ==================== TOUR DETAIL & INTERACTIONS ====================
    # POST /tours/<slug>/review/ - Kërkimi për vlerësim
    path("<slug:slug>/review/", views.create_review, name="create_review"),
    
    
    # ==================== TOUR MANAGEMENT ====================
    # POST /tours/<slug>/edit/ - Redaktimi i turit
    path("<slug:slug>/edit/", views.edit_tour, name="edit_tour"),
    
    # POST /tours/<slug>/delete/ - Fshirja e turit
    path("<slug:slug>/delete/", views.delete_tour, name="delete_tour"),
    
    # POST /tours/<slug>/pricing/ - Redaktimi i çmimeve
    path("<slug:slug>/pricing/", views.edit_tour_pricing, name="edit_tour_pricing"),
    
    # GET /tours/<slug>/stats/ - Statistika të detalizuara
    path("<slug:slug>/stats/", views.tour_statistics, name="tour_statistics"),
    
    
    # ==================== TOUR IMAGES ====================
    # POST /tours/<slug>/add-image/ - Shtim i fotos shtesë
    path("<slug:slug>/add-image/", views.add_tour_image, name="add_tour_image"),
    
    # POST /tours/image/<image_id>/delete/ - Fshirja e fotos
    path("image/<int:image_id>/delete/", views.delete_tour_image, name="delete_tour_image"),
    
    
    # ==================== TOUR SCHEDULES (ITINERARY) ====================
    # POST /tours/<slug>/add-schedule/ - Shtim i programit ditor
    path("<slug:slug>/add-schedule/", views.add_tour_schedule, name="add_tour_schedule"),
    
    # POST /tours/schedule/<schedule_id>/edit/ - Redaktimi i programit
    path("schedule/<int:schedule_id>/edit/", views.edit_tour_schedule, name="edit_tour_schedule"),
    
    # POST /tours/schedule/<schedule_id>/delete/ - Fshirja e programit
    path("schedule/<int:schedule_id>/delete/", views.delete_tour_schedule, name="delete_tour_schedule"),
    
    
    # ==================== TOUR FAQ ====================
    # POST /tours/<slug>/add-faq/ - Shtim i pyetjeve të shpeshta
    path("<slug:slug>/add-faq/", views.add_tour_faq, name="add_tour_faq"),
    
    # POST /tours/faq/<faq_id>/edit/ - Redaktimi i FAQ
    path("faq/<int:faq_id>/edit/", views.edit_tour_faq, name="edit_tour_faq"),
    
    # POST /tours/faq/<faq_id>/delete/ - Fshirja e FAQ
    path("faq/<int:faq_id>/delete/", views.delete_tour_faq, name="delete_tour_faq"),
    
    
    # ==================== TOUR REVIEWS ====================
    # POST /tours/review/<review_id>/edit/ - Redaktimi i vlerësimit
    path("review/<int:review_id>/edit/", views.edit_review, name="edit_review"),
    
    # POST /tours/review/<review_id>/delete/ - Fshirja e vlerësimit
    path("review/<int:review_id>/delete/", views.delete_review, name="delete_review"),
    
    # ==================== TOUR STATUS (AJAX) ====================
    # GET /tours/api/status/<tour_id>/ - Merr statusin aktual të turit
    path("api/status/<int:tour_id>/", status_views.get_tour_status, name="get_tour_status"),
    
    # POST /tours/api/status/update/ - Përditëso statusin e turit
    path("api/status/update/", status_views.update_tour_status, name="update_tour_status"),
    
    # GET /tours/api/guide-tours-status/ - Merr statusin e të gjithë tureve të guide-it
    path("api/guide-tours-status/", status_views.get_guide_tours_status, name="get_guide_tours_status"),
    
    # ==================== TOUR DETAIL (must come last) ====================
    # GET /tours/<slug>/ - Detajet e turit
    path("<slug:slug>/", TourDetailView.as_view(), name="tour_detail"),
]