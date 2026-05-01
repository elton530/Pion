from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, ListView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage

from users.models import GuideProfile
from .models import Tour, TourReview, TourImage, TourSchedule, TourFAQ, TourStatistic
from .forms import (
    TourCreateForm, TourEditForm, TourReviewForm, TourImageForm,
    TourScheduleForm, TourFAQForm, TourSearchForm, TourPricingForm
)


# ==================== TOUR LIST VIEWS ====================

class TourListView(ListView):
    """Shfaqet listën e tureve me filtrimin dhe kërkimin"""
    
    model = Tour
    template_name = "tours/tour_list.html"
    context_object_name = "tours"
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Tour.objects.filter(
            is_active=True,
            status="published",
            date__gte=timezone.now().date()
        ).select_related("guide__user").prefetch_related("images", "reviews")
        # Precompute approved reviews average to avoid per-item queries
        # Note: do NOT annotate `reviews_count` because it's a real model field
        # on `Tour` (conflicts with annotations). Use the stored field instead.
        queryset = queryset.annotate(
            avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
        )
        
        # Kërkimi sipas titullit ose përshkrimit
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(short_description__icontains=search) |
                Q(full_description__icontains=search)
            )
        
        # Filtrimi sipas lokacionit
        location = self.request.GET.get('location', '').strip()
        if location:
            queryset = queryset.filter(
                Q(location_city__icontains=location) |
                Q(location_region__icontains=location)
            )
        
        # Filtrimi sipas llojit të turit
        tour_type = self.request.GET.get('tour_type', '').strip()
        if tour_type:
            queryset = queryset.filter(tour_type=tour_type)
        
        # Filtrimi sipas vshtirësisë
        difficulty = self.request.GET.get('difficulty', '').strip()
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Filtrimi sipas grupit moshor
        age_group = self.request.GET.get('age_group', '').strip()
        if age_group:
            queryset = queryset.filter(age_group=age_group)
        
        # Filtrimi sipas gamës çmimesh
        try:
            min_price = self.request.GET.get('min_price')
            if min_price:
                queryset = queryset.filter(price_per_person__gte=float(min_price))
            
            max_price = self.request.GET.get('max_price')
            if max_price:
                queryset = queryset.filter(price_per_person__lte=float(max_price))
        except (ValueError, TypeError):
            pass
        
        # Filtrimi sipas datës
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Rendimi i rezultateve
        sort_by = self.request.GET.get('sort_by', '-date')
        if sort_by in ['-date', 'date', 'price_per_person', '-price_per_person', 
                       '-average_rating', '-created_at', 'booking_percentage']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TourSearchForm(self.request.GET)
        context['current_search'] = self.request.GET.urlencode()
        
        # Statistika
        # Use the same queryset as the list to keep filters consistent
        context['total_tours'] = self.get_queryset().count()
        
        return context


class TourSearchView(ListView):
    """Kërkimi i avancuar i tureve"""
    
    model = Tour
    template_name = "tours/tour_search.html"
    context_object_name = "tours"
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Tour.objects.filter(
            is_active=True,
            status="published"
        ).select_related("guide__user")
        
        form = TourSearchForm(self.request.GET)
        if form.is_valid():
            # Kërkimi
            if form.cleaned_data.get('search'):
                search = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(short_description__icontains=search)
                )
            
            # Lokacioni
            if form.cleaned_data.get('location'):
                queryset = queryset.filter(
                    location_city__icontains=form.cleaned_data['location']
                )
            
            # Lloji i turit
            tour_types = form.cleaned_data.get('tour_type')
            if tour_types:
                queryset = queryset.filter(tour_type__in=tour_types)
            
            # Vshtirësia
            difficulties = form.cleaned_data.get('difficulty')
            if difficulties:
                queryset = queryset.filter(difficulty__in=difficulties)
            
            # Grupi moshor
            if form.cleaned_data.get('age_group'):
                queryset = queryset.filter(age_group=form.cleaned_data['age_group'])
            
            # Çmimi
            if form.cleaned_data.get('min_price'):
                queryset = queryset.filter(
                    price_per_person__gte=form.cleaned_data['min_price']
                )
            
            if form.cleaned_data.get('max_price'):
                queryset = queryset.filter(
                    price_per_person__lte=form.cleaned_data['max_price']
                )
            
            # Data
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(date__gte=form.cleaned_data['date_from'])
            
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(date__lte=form.cleaned_data['date_to'])
            
            # Rendimi
            sort_by = form.cleaned_data.get('sort_by', '-date')
            if sort_by:
                queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TourSearchForm(self.request.GET)
        return context


# ==================== TOUR DETAIL VIEW ====================

class TourDetailView(DetailView):
    """Shfaqja e detajeve të një turi"""
    
    model = Tour
    template_name = "tours/tour_detail.html"
    context_object_name = "tour"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    
    def get_queryset(self):
        # Allow published tours for everyone, but let the guide owner view their
        # own tours (including drafts) while editing. This keeps unpublished
        # drafts hidden from public users.
        base_qs = Tour.objects.filter(is_active=True).select_related(
            "guide__user"
        ).prefetch_related("images", "reviews", "schedules", "faqs")

        # Public users only see published tours
        if not self.request.user.is_authenticated:
            return base_qs.filter(status="published")

        # If the current user is the guide owner, allow them to access their
        # own tours regardless of status; otherwise only published tours.
        try:
            if hasattr(self.request.user, "guide_profile"):
                guide_profile = self.request.user.guide_profile
                return base_qs.filter(Q(status="published") | Q(guide=guide_profile))
        except Exception:
            # Fall back to published only if anything goes wrong
            pass

        return base_qs.filter(status="published")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tour = self.object
        
        # Imazhet - filter out media files that are missing from storage
        valid_images = []
        for img in tour.images.all():
            try:
                if img.image and default_storage.exists(img.image.name):
                    valid_images.append(img)
            except Exception:
                # skip images that cause storage errors
                continue
        context["additional_images"] = valid_images

        # Check main image exists before rendering to avoid 404s
        main_image_exists = False
        try:
            if tour.main_image and default_storage.exists(tour.main_image.name):
                main_image_exists = True
        except Exception:
            main_image_exists = False
        context["main_image_exists"] = main_image_exists
        
        # Vlerësimet
        context["reviews"] = tour.reviews.filter(
            is_approved=True
        ).select_related("tourist__user")[:10]
        context["featured_reviews"] = tour.reviews.filter(
            is_approved=True,
            is_featured=True
        ).select_related("tourist__user")[:3]
        
        # Numri i vlerësimeve për çdo notë
        context["rating_distribution"] = tour.reviews.filter(
            is_approved=True
        ).values('rating').annotate(count=Count('id')).order_by('rating')
        
        # Forma e vlerësimit
        context["review_form"] = TourReviewForm()
        context["can_review"] = False
        context["user_review"] = None
        
        # Kontrollo nëse përdoruesi mund të lërë review
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, "tourist_profile"):
                context["can_review"] = True
                try:
                    context["user_review"] = tour.reviews.get(
                        tourist=self.request.user.tourist_profile
                    )
                except TourReview.DoesNotExist:
                    pass
        
        # Turet e ngjashëm
        context["recommended_tours"] = tour.get_recommended_tours(limit=3)
        
        # Programi ditor (për turet shumë-ditore)
        context["schedules"] = tour.schedules.all().order_by('day_number')
        
        # FAQ
        context["faqs"] = tour.faqs.filter(is_active=True)
        # Current timestamp for template comparisons (discounts, early bird)
        context["now"] = timezone.now()
        
        # Statistika
        try:
            stats = tour.statistics
            stats.increment_views(unique=False)
            context["tour_views"] = stats.views
        except TourStatistic.DoesNotExist:
            TourStatistic.objects.create(tour=tour)
        
        return context


# ==================== TOUR CREATE/EDIT VIEWS ====================

@login_required
def create_tour(request):
    """Krijimi i një turi të ri"""
    
    # Kontrollo nëse përdoruesi është Guide
    try:
        guide_profile = request.user.guide_profile
    except GuideProfile.DoesNotExist:
        messages.error(
            request,
            "Vetëm guidat mund të krijojnë ture. Plotëso profilin tënd së pari!"
        )
        return redirect("users:guide_profile_edit")
    
    if request.method == "POST":
        form = TourCreateForm(request.POST, request.FILES)
        if form.is_valid():
            tour = form.save(commit=False)
            tour.guide = guide_profile
            # Publish new tours by default so they appear in listings immediately.
            # If you prefer a draft workflow, change this back to 'draft' or
            # add a publish checkbox to the form.
            tour.status = "published"
            tour.save()
            
            messages.success(
                request,
                f'Turi "{tour.title}" u krijua me sukses! Tani plotëso detajet shtesë.'
            )
            return redirect("tours:edit_tour", slug=tour.slug)
        else:
            messages.error(request, "Ka gabime në formë. Provo përsëri.")
    else:
        form = TourCreateForm()
    
    return render(request, "tours/create_tour.html", {"form": form})


@login_required
def edit_tour(request, slug):
    """Redaktimi i një turi"""
    
    tour = get_object_or_404(Tour, slug=slug)
    
    # Kontrollo nëse përdoruesi është owner i turit
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund ta redaktosh turin e një guide tjetër.")
    
    if request.method == "POST":
        form = TourEditForm(request.POST, request.FILES, instance=tour)
        if form.is_valid():
            form.save()
            messages.success(request, f'Turi "{tour.title}" u përditësua me sukses!')
            return redirect("tours:tour_detail", slug=tour.slug)
        else:
            messages.error(request, "Ka gabime në formë. Provo përsëri.")
    else:
        form = TourEditForm(instance=tour)
    
    return render(request, "tours/edit_tour.html", {
        "form": form,
        "tour": tour
    })


@login_required
def delete_tour(request, slug):
    """Fshirja e një turi"""
    
    tour = get_object_or_404(Tour, slug=slug)
    
    # Kontrollo nëse përdoruesi është owner
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund ta fshish turin e një guide tjetër.")
    
    if request.method == "POST":
        title = tour.title
        tour.delete()
        messages.success(request, f'Turi "{title}" u fshi me sukses!')
        return redirect("tours:my_tours")
    
    return render(request, "tours/delete_tour.html", {"tour": tour})


# ==================== GUIDE'S TOURS VIEW ====================

@login_required
def my_tours(request):
    """Shfaqja e tureve të guide-it"""
    
    try:
        guide_profile = request.user.guide_profile
    except GuideProfile.DoesNotExist:
        messages.error(request, "Nuk je i regjistruar si guide.")
        return redirect("users:guide_profile_edit")
    
    status_filter = request.GET.get('status', 'all')
    
    base_qs = guide_profile.tours.all()
    tours = base_qs.order_by('-created_at')

    if status_filter != 'all':
        tours = tours.filter(status=status_filter)

    # Statistika using aggregate to avoid iterating in Python
    aggregates = base_qs.aggregate(total_bookings=Sum('booking_count'))
    total_bookings = aggregates.get('total_bookings') or 0

    context = {
        'tours': tours,
        'status_filter': status_filter,
        'total_tours': base_qs.count(),
        'published_tours': base_qs.filter(status='published').count(),
        'draft_tours': base_qs.filter(status='draft').count(),
        'total_bookings': total_bookings,
        'total_reviews': TourReview.objects.filter(
            tour__guide=guide_profile,
            is_approved=True
        ).count(),
    }
    
    return render(request, "tours/my_tours.html", context)


# ==================== TOUR PRICING VIEW ====================

@login_required
def edit_tour_pricing(request, slug):
    """Redaktimi i çmimeve dhe zbritjeve"""
    
    tour = get_object_or_404(Tour, slug=slug)
    
    # Kontrollo nëse përdoruesi është owner
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund ta redaktosh çmimin e një turi të tjerë.")
    
    if request.method == "POST":
        form = TourPricingForm(request.POST, instance=tour)
        if form.is_valid():
            form.save()
            messages.success(request, "Çmimet u përditësuan me sukses!")
            return redirect("tours:tour_detail", slug=tour.slug)
    else:
        form = TourPricingForm(instance=tour)
    
    return render(request, "tours/edit_tour_pricing.html", {
        "form": form,
        "tour": tour
    })


# ==================== TOUR IMAGES VIEWS ====================

@login_required
def add_tour_image(request, slug):
    """Shtim i fotos shtesë"""
    
    tour = get_object_or_404(Tour, slug=slug)
    
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund t'i shtosh foto turit të një guide tjetër.")
    
    if request.method == "POST":
        form = TourImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.tour = tour
            image.save()
            messages.success(request, "Foto u shtua me sukses!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Foto u shtua me sukses!'})
            
            return redirect("tours:edit_tour", slug=slug)
    else:
        form = TourImageForm()
    
    return render(request, "tours/add_tour_image.html", {
        "form": form,
        "tour": tour
    })


@login_required
def delete_tour_image(request, image_id):
    """Fshirja e fotos"""
    
    image = get_object_or_404(TourImage, id=image_id)
    tour = image.tour
    
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund ta fshish foton e turit të një guide tjetër.")
    
    image.delete()
    messages.success(request, "Foto u fshi me sukses!")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect("tours:edit_tour", slug=tour.slug)


# ==================== TOUR SCHEDULE VIEWS ====================

@login_required
def add_tour_schedule(request, slug):
    """Shtim i programit ditor"""
    
    tour = get_object_or_404(Tour, slug=slug)
    
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund t'i shtosh programa turit të një guide tjetër.")
    
    if request.method == "POST":
        form = TourScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.tour = tour
            schedule.save()
            messages.success(request, "Programi u shtua me sukses!")
            return redirect("tours:edit_tour", slug=slug)
    else:
        form = TourScheduleForm()
    
    return render(request, "tours/add_tour_schedule.html", {
        "form": form,
        "tour": tour
    })


@login_required
def edit_tour_schedule(request, schedule_id):
    """Redaktimi i programit ditor"""
    
    schedule = get_object_or_404(TourSchedule, id=schedule_id)
    tour = schedule.tour
    
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund ta redaktosh programin e turit të një guide tjetër.")
    
    if request.method == "POST":
        form = TourScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, "Programi u përditësua me sukses!")
            return redirect("tours:edit_tour", slug=tour.slug)
    else:
        form = TourScheduleForm(instance=schedule)
    
    return render(request, "tours/edit_tour_schedule.html", {
        "form": form,
        "schedule": schedule
    })


@login_required
def delete_tour_schedule(request, schedule_id):
    """Fshirja e programit ditor"""
    
    schedule = get_object_or_404(TourSchedule, id=schedule_id)
    tour = schedule.tour
    
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund ta fshish programin e turit të një guide tjetër.")
    
    schedule.delete()
    messages.success(request, "Programi u fshi me sukses!")
    return redirect("tours:edit_tour", slug=tour.slug)


# ==================== TOUR FAQ VIEWS ====================

@login_required
def add_tour_faq(request, slug):
    """Shtim i pyetjeve të shpeshta"""
    
    tour = get_object_or_404(Tour, slug=slug)
    
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund t'i shtosh FAQ turit të një guide tjetër.")
    
    if request.method == "POST":
        form = TourFAQForm(request.POST)
        if form.is_valid():
            faq = form.save(commit=False)
            faq.tour = tour
            faq.save()
            messages.success(request, "Pyetja u shtua me sukses!")
            return redirect("tours:edit_tour", slug=slug)
    else:
        form = TourFAQForm()
    
    return render(request, "tours/add_tour_faq.html", {
        "form": form,
        "tour": tour
    })


@login_required
def edit_tour_faq(request, faq_id):
    """Redaktimi i pyetjeve të shpeshta"""
    
    faq = get_object_or_404(TourFAQ, id=faq_id)
    tour = faq.tour
    
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund ta redaktosh FAQ-in e turit të një guide tjetër.")
    
    if request.method == "POST":
        form = TourFAQForm(request.POST, instance=faq)
        if form.is_valid():
            form.save()
            messages.success(request, "Pyetja u përditësua me sukses!")
            return redirect("tours:edit_tour", slug=tour.slug)
    else:
        form = TourFAQForm(instance=faq)
    
    return render(request, "tours/edit_tour_faq.html", {
        "form": form,
        "faq": faq
    })


@login_required
def delete_tour_faq(request, faq_id):
    """Fshirja e pyetjeve të shpeshta"""
    
    faq = get_object_or_404(TourFAQ, id=faq_id)
    tour = faq.tour
    
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund ta fshish FAQ-in e turit të një guide tjetër.")
    
    faq.delete()
    messages.success(request, "Pyetja u fshi me sukses!")
    return redirect("tours:edit_tour", slug=tour.slug)


# ==================== TOUR REVIEW VIEWS ====================

@login_required
def create_review(request, slug):
    """Krijimi i një vlerësimi"""
    
    tour = get_object_or_404(Tour, slug=slug, is_active=True)
    
    # Kontrollo nëse përdoruesi është turist
    if not hasattr(request.user, "tourist_profile"):
        messages.error(request, "Vetëm turistët mund të lënë vlerësime.")
        return redirect("tours:tour_detail", slug=slug)
    
    if request.method == "POST":
        form = TourReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.tour = tour
            review.tourist = request.user.tourist_profile
            review.save()
            
            messages.success(request, "Faleminderit! Vlerësimi u regjistrua.")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Vlerësimi u regjistrua!'})
        else:
            messages.error(request, "Ka gabime në formë.")
    
    return redirect("tours:tour_detail", slug=slug)


@login_required
def edit_review(request, review_id):
    """Redaktimi i një vlerësimi"""
    
    review = get_object_or_404(TourReview, id=review_id)
    
    # Kontrollo nëse përdoruesi është i autorizuar
    if review.tourist.user != request.user:
        raise PermissionDenied("Nuk mund ta redaktosh vlerësimin e një persone tjetër.")
    
    if request.method == "POST":
        form = TourReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Vlerësimi u përditësua me sukses!")
            return redirect("tours:tour_detail", slug=review.tour.slug)
    else:
        form = TourReviewForm(instance=review)
    
    return render(request, "tours/edit_review.html", {
        "form": form,
        "review": review
    })


@login_required
def delete_review(request, review_id):
    """Fshirja e një vlerësimi"""
    
    review = get_object_or_404(TourReview, id=review_id)
    
    # Kontrollo nëse përdoruesi është i autorizuar
    if review.tourist.user != request.user:
        raise PermissionDenied("Nuk mund ta fshish vlerësimin e një persone tjetër.")
    
    tour_slug = review.tour.slug
    review.delete()
    messages.success(request, "Vlerësimi u fshi me sukses!")
    return redirect("tours:tour_detail", slug=tour_slug)


# ==================== MISCELLANEOUS VIEWS ====================

def featured_tours(request):
    """Shfaqja e tureve featured"""
    
    tours = Tour.objects.filter(
        is_active=True,
        status="published",
        is_featured=True,
        featured_until__gte=timezone.now().date()
    ).select_related("guide__user")
    
    return render(request, "tours/featured_tours.html", {"tours": tours})


def tour_by_location(request, location):
    """Turet sipas lokacionit"""
    
    qs = Tour.objects.filter(
        is_active=True,
        status="published",
        location_city__icontains=location
    ).select_related("guide__user")

    tours = list(qs)
    if not tours:
        messages.info(request, f"Nuk ka ture në {location}.")

    return render(request, "tours/tour_by_location.html", {
        "tours": tours,
        "location": location
    })


@login_required
def tour_statistics(request, slug):
    """Statistika e turit (për guide-in)"""
    
    tour = get_object_or_404(Tour, slug=slug)
    
    if tour.guide.user != request.user:
        raise PermissionDenied("Nuk mund të shikosh statistikat e turit të një guide tjetër.")
    
    try:
        stats = tour.statistics
    except TourStatistic.DoesNotExist:
        stats = TourStatistic.objects.create(tour=tour)
    
    context = {
        'tour': tour,
        'stats': stats,
        'reviews_count': tour.reviews.filter(is_approved=True).count(),
        'average_rating': tour.average_rating,
        'booking_percentage': tour.booking_percentage,
    }
    
    return render(request, "tours/tour_statistics.html", context)