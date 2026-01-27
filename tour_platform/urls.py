from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

app_name = "tour_platform"

urlpatterns = [
    # ==================== ADMIN ====================
    path("admin/", admin.site.urls),
    
    
    # ==================== AUTHENTICATION & USERS ====================
    path("users/", include("users.urls")),
    
    
    # ==================== TOURS ====================
    path("tours/", include("tours.urls")),
    
    
    # ==================== BOOKINGS ====================
    path("bookings/", include("bookings.urls")),
    
    
    # ==================== CORE (HOME, ABOUT, CONTACT, ETC) ====================
    path("", include("core.urls")),
]

# ==================== STATIC & MEDIA FILES ====================
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# ==================== CUSTOM ERROR HANDLERS ====================
# handler404 = 'core.views.custom_404'
# handler500 = 'core.views.custom_500'
# handler403 = 'core.views.custom_403'