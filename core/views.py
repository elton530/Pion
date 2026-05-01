from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

from .models import ContactMessage, NewsletterSubscription, FAQ, SiteSettings, SocialLink
from .forms import (
    ContactForm, ContactFormAnonymous, ContactFormAuthenticated,
    NewsletterSubscriptionForm, NewsletterUnsubscribeForm,
    GlobalSearchForm, FeedbackForm
)
from tours.models import Tour
from users.models import GuideProfile, TouristProfile


# ==================== HOME & LANDING PAGES ====================

class HomeView(TemplateView):
    """Faqja kryesore"""
    
    template_name = "core/home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Turet më të rinj
        context['latest_tours'] = Tour.objects.filter(
            is_active=True,
            status='published'
        ).order_by('-created_at')[:6]
        
        # Turet më të vlerësuar
        context['top_rated_tours'] = Tour.objects.filter(
            is_active=True,
            status='published',
            reviews_count__gt=0
        ).order_by('-average_rating')[:6]
        
        # Guide-t më aktiv
        context['featured_guides'] = GuideProfile.objects.filter(
            is_active=True,
            is_verified=True
        ).order_by('-average_rating')[:6]
        
        # Statistika
        context['total_tours'] = Tour.objects.filter(
            is_active=True,
            status='published'
        ).count()
        context['total_guides'] = GuideProfile.objects.filter(
            is_active=True,
            is_verified=True
        ).count()
        context['total_reviews'] = Tour.objects.filter(
            reviews_count__gt=0
        ).aggregate(total=Count('reviews_count'))['total'] or 0
        # Aliases used by templates / JS
        context['tours_count'] = context['total_tours']
        context['guides_count'] = context['total_guides']

        # Upcoming tours (by date) for the homepage
        try:
            today = timezone.now().date()
            context['upcoming_tours'] = Tour.objects.filter(
                is_active=True,
                status='published',
                date__gte=today
            ).order_by('date')[:8]
        except Exception:
            context['upcoming_tours'] = context.get('latest_tours', [])
        
        # Newsletter form
        context['newsletter_form'] = NewsletterSubscriptionForm()
        
        # Social links
        context['social_links'] = SocialLink.objects.filter(is_active=True).order_by('order')
        
        return context


class AboutView(TemplateView):
    """Faqja "Rreth Nesh" """
    
    template_name = "core/about.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistika
        context['total_tours'] = Tour.objects.filter(
            is_active=True,
            status='published'
        ).count()
        context['total_guides'] = GuideProfile.objects.filter(
            is_active=True,
            is_verified=True
        ).count()
        context['total_tourists'] = TouristProfile.objects.count()
        context['total_bookings'] = Tour.objects.aggregate(
            total=Count('bookings')
        )['total'] or 0
        
        return context


# ==================== CONTACT ====================

def contact(request):
    """Faqja e kontaktit"""
    
    if request.method == "POST":
        # Zgjedh formën bazuar në statusin e logimit
        if request.user.is_authenticated:
            form = ContactFormAuthenticated(request.POST, user=request.user)
        else:
            form = ContactFormAnonymous(request.POST)
        
        if form.is_valid():
            contact_msg = form.save()
            
            # Dërgoni email te admin
            try:
                admin_emails = [admin[1] for admin in settings.ADMINS]
                if admin_emails:
                    subject = f"📬 Mesazh i ri kontakti: {contact_msg.subject}"
                    context = {
                        'name': contact_msg.name,
                        'email': contact_msg.email,
                        'phone': contact_msg.phone or 'N/A',
                        'subject': contact_msg.subject,
                        'message': contact_msg.message,
                        'created_at': contact_msg.created_at,
                    }
                    # message = render_to_string('emails/new_contact.html', context)
                    message = f"Mesazh i ri: {contact_msg.subject}"
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        admin_emails,
                        fail_silently=True
                    )
            except Exception as e:
                print(f"Gabim në dërgimin e email: {e}")
            
            messages.success(
                request,
                "✅ Faleminderit! Mesazhi juaj u dërgua. Do t'ju kontaktojmë në brëndësi të 24 orëve."
            )
            return redirect("core:contact")
    
    else:
        if request.user.is_authenticated:
            form = ContactFormAuthenticated(user=request.user)
        else:
            form = ContactFormAnonymous()
    
    context = {
        'form': form,
        'settings': SiteSettings.get_settings(),
        'social_links': SocialLink.objects.filter(is_active=True).order_by('order'),
    }
    
    return render(request, "core/contact.html", context)


@login_required
def contact_list(request):
    """Lista e mesazheve për admin"""
    
    if not request.user.is_staff:
        messages.error(request, "❌ Nuk ke akses në këtë faqe.")
        return redirect("home")
    
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    
    # Filtrim
    status = request.GET.get('status')
    if status:
        messages_list = messages_list.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        messages_list = messages_list.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(subject__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'new_count': ContactMessage.objects.filter(status='new').count(),
    }
    
    return render(request, "core/contact_list.html", context)


@login_required
def contact_detail(request, contact_id):
    """Detajet e një mesazhi"""
    
    if not request.user.is_staff:
        messages.error(request, "❌ Nuk ke akses.")
        return redirect("home")
    
    contact_msg = get_object_or_404(ContactMessage, id=contact_id)
    
    if request.method == "POST":
        reply = request.POST.get('reply_message', '').strip()
        
        if reply:
            contact_msg.mark_as_replied(reply, request.user)
            
            # Dërgoni email përgjigjeje
            try:
                subject = f"Re: {contact_msg.subject}"
                # message = render_to_string('emails/contact_reply.html', {'reply': reply})
                message = f"Përgjigjja ynë: {reply}"
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [contact_msg.email],
                    fail_silently=True
                )
            except:
                pass
            
            messages.success(request, "✅ Përgjigja u dërgua.")
            return redirect("core:contact_detail", contact_id=contact_msg.id)
    
    context = {'contact': contact_msg}
    return render(request, "core/contact_detail.html", context)


# ==================== FAQ ====================

class FAQListView(ListView):
    """Lista e pyetjeve të shpeshta"""
    
    model = FAQ
    template_name = "core/faq_list.html"
    context_object_name = "faqs"
    paginate_by = 20
    
    def get_queryset(self):
        return FAQ.objects.filter(is_active=True).order_by('category', 'order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Kategorite
        context['categories'] = FAQ.objects.filter(
            is_active=True
        ).values('category').distinct()
        
        # Kategoria aktive
        context['active_category'] = self.request.GET.get('category', 'all')
        
        return context
    
    def get_queryset(self):
        queryset = FAQ.objects.filter(is_active=True).order_by('category', 'order')
        
        category = self.request.GET.get('category')
        if category and category != 'all':
            queryset = queryset.filter(category=category)
        
        return queryset


class FAQDetailView(DetailView):
    """Detajet e një pyetje"""
    
    model = FAQ
    template_name = "core/faq_detail.html"
    context_object_name = "faq"
    
    def get_queryset(self):
        return FAQ.objects.filter(is_active=True)
    
    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        obj.increment_views()
        return obj


# ==================== NEWSLETTER ====================

def newsletter_subscribe(request):
    """Nënshkrim në newsletter"""
    
    if request.method == "POST":
        form = NewsletterSubscriptionForm(request.POST)
        
        if form.is_valid():
            subscription = form.save()
            
            # Dërgoni email confirmimi
            try:
                subject = "✅ Nënshkrim në newsletter të Tour Platform Albania"
                context = {'email': subscription.email}
                # message = render_to_string('emails/newsletter_welcome.html', context)
                message = "Faleminderit për nënshkrimin! Pritet me lajmet më të reja."
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [subscription.email],
                    fail_silently=True
                )
            except:
                pass
            
            messages.success(
                request,
                "✅ Faleminderit për nënshkrimin! Kontrolloni email-in tuaj."
            )
            return redirect("core:home")
    
    else:
        form = NewsletterSubscriptionForm()
    
    context = {'form': form}
    return render(request, "core/newsletter_subscribe.html", context)


def newsletter_unsubscribe(request):
    """Anulim nënshkrimi"""
    
    if request.method == "POST":
        form = NewsletterUnsubscribeForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            subscription = NewsletterSubscription.objects.get(email=email)
            subscription.unsubscribe()
            
            messages.success(
                request,
                "✅ Nënshkrimi u anullua. Nuk do t'ju dërgojmë më email-a."
            )
            return redirect("core:home")
    
    else:
        form = NewsletterUnsubscribeForm()
    
    context = {'form': form}
    return render(request, "core/newsletter_unsubscribe.html", context)


# ==================== SEARCH ====================

def global_search(request):
    """Kërkimi global"""
    
    form = GlobalSearchForm(request.GET)
    results = {
        'tours': [],
        'guides': [],
        'locations': [],
    }
    query = None
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        search_type = form.cleaned_data.get('search_type', 'all')
        
        if query:
            if search_type in ['all', 'tours']:
                results['tours'] = Tour.objects.filter(
                    Q(title__icontains=query) |
                    Q(short_description__icontains=query),
                    is_active=True,
                    status='published'
                )[:10]
            
            if search_type in ['all', 'guides']:
                results['guides'] = GuideProfile.objects.filter(
                    Q(user__first_name__icontains=query) |
                    Q(user__last_name__icontains=query) |
                    Q(location__icontains=query),
                    is_active=True,
                    is_verified=True
                )[:10]
            
            if search_type in ['all', 'locations']:
                results['locations'] = Tour.objects.filter(
                    Q(location_city__icontains=query) |
                    Q(location_region__icontains=query),
                    is_active=True,
                    status='published'
                ).values('location_city', 'location_region').distinct()[:10]
    
    context = {
        'form': form,
        'query': query,
        'results': results,
        'total_results': sum(len(r) if isinstance(r, (list, type(Tour.objects.none()))) else 0 
                            for r in results.values()),
    }
    
    return render(request, "core/search_results.html", context)


# ==================== FEEDBACK ====================

def submit_feedback(request):
    """Dërgim feedback"""
    
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        
        if form.is_valid():
            # Ruaj feedback (mund të krijohet model nëse duhet)
            rating = form.cleaned_data['rating']
            comment = form.cleaned_data['comment']
            email = form.cleaned_data['email']
            
            # Dërgoni email te admin
            try:
                admin_emails = [admin[1] for admin in settings.ADMINS]
                if admin_emails:
                    subject = f"⭐ Feedback i ri: {rating} yje"
                    message = f"Vlerësim: {rating}\nKoment: {comment}\nEmail: {email}"
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        admin_emails,
                        fail_silently=True
                    )
            except:
                pass
            
            messages.success(
                request,
                "✅ Faleminderit për feedback-un! Vlerësimet tuaja na ndihmojnë të përmirësohemi."
            )
            return redirect("core:home")
    
    else:
        form = FeedbackForm()
    
    context = {'form': form}
    return render(request, "core/feedback.html", context)


# ==================== LEGAL PAGES ====================

class TermsView(TemplateView):
    """Kushtet dhe kondicionet"""
    
    template_name = "core/terms.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = SiteSettings.get_settings()
        return context


class PrivacyView(TemplateView):
    """Politika e privatësisë"""
    
    template_name = "core/privacy.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = SiteSettings.get_settings()
        return context