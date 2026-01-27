from django.urls import path
from . import views

app_name = "core"

# Pattern: /...

urlpatterns = [
    # ==================== LANDING PAGES ====================
    # GET / - Faqja kryesore
    path(
        "",
        views.HomeView.as_view(),
        name="home"
    ),
    
    # GET /rreth-nesh/ - Rreth nesh
    path(
        "rreth-nesh/",
        views.AboutView.as_view(),
        name="about"
    ),
    
    
    # ==================== CONTACT ====================
    # GET/POST /kontakt/ - Forma e kontaktit
    path(
        "kontakt/",
        views.contact,
        name="contact"
    ),
    
    # GET /kontakt/mesazhe/ - Lista e mesazheve (admin)
    path(
        "kontakt/mesazhe/",
        views.contact_list,
        name="contact_list"
    ),
    
    # GET /kontakt/mesazh/<id>/ - Detajet e mesazhit
    path(
        "kontakt/mesazh/<int:contact_id>/",
        views.contact_detail,
        name="contact_detail"
    ),
    
    
    # ==================== FAQ ====================
    # GET /pyetje-te-shpeshta/ - Lista e pyetjeve
    path(
        "pyetje-te-shpeshta/",
        views.FAQListView.as_view(),
        name="faq_list"
    ),
    
    # GET /pyetje/<int:pk>/ - Detajet e pyetjes
    path(
        "pyetje/<int:pk>/",
        views.FAQDetailView.as_view(),
        name="faq_detail"
    ),
    
    
    # ==================== NEWSLETTER ====================
    # POST /newsletter/nenshkrim/ - Nënshkrim newsletter
    path(
        "newsletter/nenshkrim/",
        views.newsletter_subscribe,
        name="newsletter_subscribe"
    ),
    
    # GET/POST /newsletter/anullim/ - Anulim nënshkrimi
    path(
        "newsletter/anullim/",
        views.newsletter_unsubscribe,
        name="newsletter_unsubscribe"
    ),
    
    
    # ==================== SEARCH ====================
    # GET /kerko/ - Kërkimi global
    path(
        "kerko/",
        views.global_search,
        name="global_search"
    ),
    
    
    # ==================== FEEDBACK ====================
    # POST /feedback/ - Dërgim feedback
    path(
        "feedback/",
        views.submit_feedback,
        name="submit_feedback"
    ),
    
    
    # ==================== LEGAL PAGES ====================
    # GET /kushte-dhe-kondicion/ - Kushtet dhe kondicionet
    path(
        "kushte-dhe-kondicion/",
        views.TermsView.as_view(),
        name="terms"
    ),
    
    # GET /politika-e-privatesi/ - Politika e privatësisë
    path(
        "politika-e-privatesi/",
        views.PrivacyView.as_view(),
        name="privacy"
    ),
]