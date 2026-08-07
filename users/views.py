from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage

from .forms import (
    SignupForm, GuideProfileForm, GuideEditProfileForm,
    TouristProfileForm, TouristEditProfileForm,
    UserAuthenticationForm, CustomPasswordChangeForm
)
from .models import GuideProfile, TouristProfile
from tours.models import Tour, TourReview
from bookings.models import Booking


# ==================== AUTHENTICATION VIEWS ====================

def signup(request):
    """Signup view për të rinj përdorues"""
    
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data.get("role")

            if role == "guide":
                user.is_active = False
                user.save()
                form.save_m2m() if hasattr(form, 'save_m2m') else None

                GuideProfile.objects.get_or_create(user=user)
                guide_profile = GuideProfile.objects.get(user=user)
                guide_profile.status = "pending"
                guide_profile.is_verified = False
                guide_profile.is_active = False
                guide_profile.save(update_fields=["status", "is_verified", "is_active", "updated_at"])

                messages.success(
                    request,
                    "🎉 Regjistrimi u krye me sukses. Llogaria juaj si guide do të aktivizohet pas miratimit të administratorit."
                )
                return redirect("users:login")

            user.save()
            login(request, user)
            messages.success(
                request,
                f"🎉 Mirëseerdhët {user.first_name}! Llogaria u krijua me sukses."
            )
            messages.info(request, "✅ Paneli juaj është gati.")
            return redirect("core:home")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignupForm()
    
    return render(request, "users/signup.html", {"form": form})


class CustomLoginView(LoginView):
    """Custom login view me redirect bazuar në rolin e përdoruesit"""
    
    template_name = "users/login.html"
    form_class = UserAuthenticationForm
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Verifiko kredencialet"""
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        # Provo login me username ose email
        from django.contrib.auth.models import User
        user = None
        
        try:
            user_obj = User.objects.get(username=username)
            user = authenticate(request=self.request, username=username, password=password)
        except User.DoesNotExist:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request=self.request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f"✅ Mirëseerdhët, {user.first_name or user.username}!")
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, "❌ Username/email ose fjalëkalim i gabuar.")
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Redirect bazuar në rolin e përdoruesit"""
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return reverse_lazy("users:admin_dashboard")

        try:
            if GuideProfile.objects.filter(user=user).exists():
                return reverse_lazy("users:guide_dashboard")
        except:
            pass
        
        try:
            if TouristProfile.objects.filter(user=user).exists():
                return reverse_lazy("users:tourist_dashboard")
        except:
            pass
        
        return reverse_lazy("core:home")


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    
    next_page = 'core:home'
    
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "✅ Ju shkëputët me sukses.")
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordChangeView(PasswordChangeView):
    """Ndryshim fjalëkalimi"""
    
    form_class = CustomPasswordChangeForm
    template_name = "users/password_change.html"
    success_url = reverse_lazy("users:password_change_done")
    
    def form_valid(self, form):
        messages.success(self.request, "✅ Fjalëkalimi u ndryshua me sukses.")
        return super().form_valid(form)


@user_passes_test(lambda u: u.is_active and (u.is_staff or u.is_superuser))
def admin_dashboard(request):
    """Dashboard i administratorit për miratimin e guide-ve dhe monitorimin e platformës."""
    pending_guides = GuideProfile.objects.filter(status="pending").select_related("user").order_by("-created_at")
    verified_guides = GuideProfile.objects.filter(status="verified").select_related("user").order_by("-verified_at", "-updated_at")
    rejected_guides = GuideProfile.objects.filter(status="rejected").select_related("user").order_by("-updated_at")
    suspended_guides = GuideProfile.objects.filter(status="suspended").select_related("user").order_by("-updated_at")

    # ===== Statistika të pasuruara për guide-t e miratuar =====
    verified_ids = [g.id for g in verified_guides]
    if verified_ids:
        booking_stats = (
            Booking.objects.filter(tour__guide_id__in=verified_ids)
            .values("tour__guide_id")
            .annotate(
                booking_count=Count("id"),
                tourist_count=Count("tourist", distinct=True),
                revenue=Sum(
                    "final_price",
                    filter=Q(status__in=["confirmed", "completed"]),
                ),
            )
        )
        guide_booking_stats = {row["tour__guide_id"]: row for row in booking_stats}

        tour_counts = dict(
            Tour.objects.filter(guide_id__in=verified_ids, is_active=True)
            .values_list("guide_id")
            .annotate(c=Count("id"))
            .order_by()
        )
    else:
        guide_booking_stats = {}
        tour_counts = {}

    for guide in verified_guides:
        stats = guide_booking_stats.get(guide.id, {})
        guide.admin_tour_count = tour_counts.get(guide.id, 0)
        guide.admin_booking_count = stats.get("booking_count", 0)
        guide.admin_tourist_count = stats.get("tourist_count", 0)
        guide.admin_revenue = stats.get("revenue") or 0

    verified_count = verified_guides.count()
    total_tourists = TouristProfile.objects.count()
    total_tours = Tour.objects.count()
    active_tours = Tour.objects.filter(is_active=True, status="published").count()
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status="pending").count()
    confirmed_bookings = Booking.objects.filter(status="confirmed").count()
    completed_bookings = Booking.objects.filter(status="completed").count()
    platform_revenue = Booking.objects.filter(status__in=["confirmed", "completed"]).aggregate(
        total=Sum("final_price")
    )["total"] or 0

    recent_bookings = Booking.objects.select_related("tour", "tourist__user").order_by("-created_at")[:5]

    if request.method == "POST":
        guide_id = request.POST.get("guide_id")
        action = request.POST.get("action")
        if guide_id and action in {"approve", "reject", "suspend", "reactivate"}:
            guide = get_object_or_404(GuideProfile, id=guide_id)
            name = guide.user.get_full_name() or guide.user.username

            if action == "approve":
                guide.status = "verified"
                guide.is_verified = True
                guide.is_active = True
                guide.verified_at = timezone.now()
                guide.user.is_active = True
                guide.user.save(update_fields=["is_active"])
                guide.save(update_fields=["status", "is_verified", "is_active", "verified_at", "updated_at"])
                messages.success(request, f"✅ Guide '{name}' u miratua.")
            elif action == "reject":
                guide.status = "rejected"
                guide.is_verified = False
                guide.is_active = False
                guide.user.is_active = False
                guide.user.save(update_fields=["is_active"])
                guide.save(update_fields=["status", "is_verified", "is_active", "updated_at"])
                messages.warning(request, f"⚠️ Guide '{name}' u refuzua.")
            elif action == "suspend":
                guide.status = "suspended"
                guide.is_active = False
                guide.user.is_active = False
                guide.user.save(update_fields=["is_active"])
                guide.save(update_fields=["status", "is_active", "updated_at"])
                messages.warning(request, f"🚫 Guide '{name}' u pezullua.")
            elif action == "reactivate":
                guide.status = "verified"
                guide.is_active = True
                guide.user.is_active = True
                guide.user.save(update_fields=["is_active"])
                guide.save(update_fields=["status", "is_active", "updated_at"])
                messages.success(request, f"✅ Guide '{name}' u riaktivizua.")
            return redirect("users:admin_dashboard")

    context = {
        "pending_guides": pending_guides,
        "pending_count": pending_guides.count(),
        "verified_guides": verified_guides,
        "verified_count": verified_count,
        "rejected_count": rejected_guides.count(),
        "rejected_guides": rejected_guides,
        "suspended_count": suspended_guides.count(),
        "suspended_guides": suspended_guides,
        "total_guides": GuideProfile.objects.count(),
        "total_users": User.objects.count(),
        "total_tourists": total_tourists,
        "total_tours": total_tours,
        "active_tours": active_tours,
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "confirmed_bookings": confirmed_bookings,
        "completed_bookings": completed_bookings,
        "platform_revenue": platform_revenue,
        "recent_bookings": recent_bookings,
    }
    return render(request, "users/admin_dashboard.html", context)


# ==================== GUIDE VIEWS ====================

@login_required
def guide_profile_edit(request):
    """Redaktim i profilit të guide-it"""
    
    try:
        profile = request.user.guide_profile
    except GuideProfile.DoesNotExist:
        messages.error(request, "❌ Nuk ke akses në këtë faqe. Duhet të jesh Guide.")
        return redirect("core:home")
    
    form_class = GuideEditProfileForm if profile.status == "verified" else GuideProfileForm
    
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profili yt u përditësua me sukses!")
            return redirect("users:guide_dashboard")
        else:
            # Surface field-specific errors so the template/messages show helpful hints
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        label = form.fields[field].label if field in form.fields else field
                        messages.error(request, f"{label}: {error}")
    else:
        form = form_class(instance=profile)
    
    # Check media existence to avoid rendering broken URLs
    photo_exists = False
    cert_exists = False
    try:
        if profile.photo and default_storage.exists(profile.photo.name):
            photo_exists = True
    except Exception:
        photo_exists = False

    try:
        if profile.certification_document and default_storage.exists(profile.certification_document.name):
            cert_exists = True
    except Exception:
        cert_exists = False

    return render(
        request,
        "users/guide_profile_edit.html",
        {"form": form, "profile": profile, "photo_exists": photo_exists, "cert_exists": cert_exists}
    )


@login_required
def guide_dashboard(request):
    """Dashboard për guide-in"""
    
    try:
        guide_profile = request.user.guide_profile
    except GuideProfile.DoesNotExist:
        messages.error(request, "❌ Kjo faqe është vetëm për guidat.")
        return redirect("core:home")
    
    # Merr turet
    tours = Tour.objects.filter(guide=guide_profile).select_related("tour_type").order_by("-date")
    
    today = timezone.now().date()
    upcoming_tours = tours.filter(
        is_active=True,
        status__in=["published", "draft"],
        date__gte=today,
    ).order_by("date")
    past_tours = tours.filter(
        Q(date__lt=today) | Q(status="completed")
    ).order_by("-date")
    
    # Merr reservimet
    bookings = Booking.objects.filter(tour__guide=guide_profile).select_related(
        "tour", "tourist__user"
    ).order_by("-created_at")
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Statistika
    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status="pending").count()
    confirmed_bookings = bookings.filter(status="confirmed").count()
    completed_bookings = bookings.filter(status="completed").count()
    cancelled_bookings = bookings.filter(status="cancelled").count()
    
    # Të ardhura (të konfirmuara e të përfunduara), të ndara sipas valutës
    revenue_bookings = bookings.filter(status__in=["confirmed", "completed"]).select_related("tour")
    revenue_by_currency = {}
    for b in revenue_bookings:
        cur = b.tour.currency or "ALL"
        revenue_by_currency[cur] = revenue_by_currency.get(cur, 0) + b.total_price
    revenue_by_currency = [
        {"currency": cur, "total": total, "label": cur}
        for cur, total in sorted(revenue_by_currency.items())
    ]
    revenue = revenue_bookings.aggregate(total=Sum("total_price"))["total"] or 0
    
    # Vlerësime
    reviews = TourReview.objects.filter(
        tour__guide=guide_profile,
        is_approved=True
    ).select_related("tourist__user", "tour")
    recent_reviews = reviews.order_by("-created_at")[:5]
    
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Shpërndarja e notave
    rating_distribution = {}
    for d in reviews.values('rating').annotate(count=Count('id')):
        rating_distribution[d['rating']] = d['count']
    
    context = {
        'guide_profile': guide_profile,
        'tours': tours,
        'upcoming_tours': upcoming_tours[:5],
        'upcoming_tours_count': upcoming_tours.count(),
        'past_tours': past_tours[:5],
        'page_obj': page_obj,
        'bookings': page_obj.object_list,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'revenue': revenue,
        'revenue_by_currency': revenue_by_currency,
        'reviews_count': reviews.count(),
        'avg_rating': round(avg_rating, 1),
        'recent_reviews': recent_reviews,
        'rating_distribution': rating_distribution,
        'total_tourists': bookings.values('tourist').distinct().count(),
    }
    
    return render(request, "users/guide_dashboard.html", context)


@login_required
def guide_booking_detail(request, booking_id):
    """Detajet e një reservimi"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tour.guide.user != request.user:
        raise PermissionDenied("Nuk ke leje për këtë veprim.")
    
    return render(request, "users/guide_booking_detail.html", {"booking": booking})


@login_required
def guide_booking_action(request, booking_id, action):
    """Veprime me reservimin (confirm, cancel)"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tour.guide.user != request.user:
        raise PermissionDenied("Nuk ke leje për këtë veprim.")
    
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")
    
    if action == "confirm":
        if booking.status == "pending":
            booking.confirm()
            messages.success(
                request,
                f"✅ Rezervimi nga {booking.tourist.user.get_full_name()} u konfirmua!"
            )
    
    elif action == "cancel":
        if booking.status != "cancelled":
            booking.cancel()
            messages.success(request, "✅ Rezervimi u anulua.")
    
    return redirect("users:guide_dashboard")


# ==================== TOURIST VIEWS ====================

@login_required
def tourist_profile_edit(request):
    """Redaktim i profilit të turistit"""
    
    try:
        profile = request.user.tourist_profile
    except TouristProfile.DoesNotExist:
        messages.error(request, "❌ Nuk ke akses në këtë faqe. Duhet të jesh Turist.")
        return redirect("core:home")
    
    if request.method == "POST":
        form = TouristEditProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profili yt u përditësua me sukses!")
            return redirect("users:tourist_dashboard")
    else:
        form = TouristEditProfileForm(instance=profile)
    
    return render(
        request,
        "users/tourist_profile_edit.html",
        {"form": form, "profile": profile}
    )


@login_required
def tourist_dashboard(request):
    """Dashboard për turistin"""
    
    try:
        tourist_profile = request.user.tourist_profile
    except TouristProfile.DoesNotExist:
        messages.error(request, "❌ Kjo faqe është vetëm për turistët.")
        return redirect("core:home")
    
    # Merr reservimet
    bookings = Booking.objects.filter(tourist=tourist_profile).select_related(
        "tour__guide__user"
    ).order_by("-tour__date")
    
    # Ndaj në active dhe past
    now = timezone.now()
    upcoming_bookings = []
    past_bookings = []
    
    for booking in bookings:
        tour_datetime = timezone.make_aware(
            timezone.datetime.combine(booking.tour.date, booking.tour.time_start)
        )
        if tour_datetime > now:
            upcoming_bookings.append(booking)
        else:
            past_bookings.append(booking)
    
    # Statistika
    total_bookings = bookings.count()
    confirmed_bookings = bookings.filter(status="confirmed").count()
    pending_bookings = bookings.filter(status="pending").count()
    cancelled_bookings = bookings.filter(status="cancelled").count()
    
    total_spent = bookings.filter(status="confirmed").aggregate(
        total=Sum("total_price")
    )["total"] or 0
    
    context = {
        'tourist_profile': tourist_profile,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_spent': total_spent,
    }
    
    return render(request, "users/tourist_dashboard.html", context)


@login_required
def tourist_booking_detail(request, booking_id):
    """Detajet e një rezervimi"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tourist.user != request.user:
        raise PermissionDenied("Nuk ke leje për këtë veprim.")
    
    return render(request, "users/tourist_booking_detail.html", {"booking": booking})


@login_required
def tourist_booking_cancel(request, booking_id):
    """Anulim i një rezervimi"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tourist.user != request.user:
        raise PermissionDenied("Nuk ke leje për këtë veprim.")
    
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")
    
    if booking.status == "cancelled":
        messages.info(request, "ℹ️ Ky rezervim është tashmë anulluar.")
    else:
        booking.cancel()
        messages.success(request, f"✅ Rezervimi për '{booking.tour.title}' u anullua.")
    
    return redirect("users:tourist_dashboard")


@login_required
def tourist_confirm_participation(request, booking_id):
    """Konfirmim i pjesëmarrjes 24h para turit"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tourist.user != request.user:
        raise PermissionDenied("Nuk ke leje për këtë veprim.")
    
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")
    
    tour_datetime = timezone.make_aware(
        timezone.datetime.combine(booking.tour.date, booking.tour.time_start)
    )
    hours_until = (tour_datetime - timezone.now()).total_seconds() / 3600
    
    if hours_until > 24:
        messages.error(
            request,
            "❌ Mund të konfirmosh vetëm 24 orë përpara fillimit të turit."
        )
    elif hours_until < 0:
        messages.error(request, "❌ Turi ka përfunduar tashmë.")
    else:
        booking.is_confirmed_24h = True
        booking.confirmed_24h_at = timezone.now()
        booking.save(update_fields=['is_confirmed_24h', 'confirmed_24h_at'])
        messages.success(
            request,
            f"✅ Pjesmarrja jote në '{booking.tour.title}' u konfirmua!"
        )
    
    return redirect("users:tourist_dashboard")


@login_required
def saved_tours(request):
    """Faqja e tureve të ruajtura për turistët dhe guidat."""

    if hasattr(request.user, "tourist_profile"):
        tourist_profile = request.user.tourist_profile
        bookings = Booking.objects.filter(tourist=tourist_profile).select_related(
            "tour__guide__user"
        ).order_by("tour__date")

        now = timezone.now()
        saved_items = []
        for booking in bookings:
            tour_datetime = timezone.make_aware(
                timezone.datetime.combine(booking.tour.date, booking.tour.time_start)
            )
            if tour_datetime > now and booking.status != "cancelled":
                saved_items.append(booking)

        context = {
            "page_title": "Ture të ruajtura",
            "page_subtitle": "Ture të planifikuara dhe të ardhshme që po ndjekësh.",
            "role": "tourist",
            "saved_items": saved_items,
            "empty_message": "Nuk ke asnjë tur të ardhshëm të ruajtur aktualisht.",
        }
        return render(request, "users/activity_page.html", context)

    if hasattr(request.user, "guide_profile"):
        guide_profile = request.user.guide_profile
        saved_items = Tour.objects.filter(
            guide=guide_profile,
            is_active=True,
            status="published",
            date__gte=timezone.now().date()
        ).order_by("date", "time_start")

        context = {
            "page_title": "Ture të ruajtura",
            "page_subtitle": "Turet aktive dhe të publikuara që po ofroni.",
            "role": "guide",
            "saved_items": saved_items,
            "empty_message": "Nuk ka asnjë tur aktiv të planifikuar për momentin.",
        }
        return render(request, "users/activity_page.html", context)

    messages.error(request, "❌ Nuk ke akses në këtë faqe.")
    return redirect("core:home")


@login_required
def history(request):
    """Faqja e historikut për turistët dhe guidat."""

    if hasattr(request.user, "tourist_profile"):
        tourist_profile = request.user.tourist_profile
        bookings = Booking.objects.filter(tourist=tourist_profile).select_related(
            "tour__guide__user"
        ).order_by("-tour__date")

        now = timezone.now()
        history_items = []
        for booking in bookings:
            tour_datetime = timezone.make_aware(
                timezone.datetime.combine(booking.tour.date, booking.tour.time_start)
            )
            if tour_datetime <= now or booking.status in ["completed", "cancelled", "no_show"]:
                history_items.append(booking)

        context = {
            "page_title": "Historiku",
            "page_subtitle": "Përvoja dhe turët e kaluara që ke ndjekur.",
            "role": "tourist",
            "history_items": history_items,
            "empty_message": "Nuk ka ende histori të turëve të tua.",
        }
        return render(request, "users/activity_page.html", context)

    if hasattr(request.user, "guide_profile"):
        guide_profile = request.user.guide_profile
        history_items = Tour.objects.filter(guide=guide_profile).filter(
            Q(date__lt=timezone.now().date()) | Q(status__in=["completed", "cancelled"]) | Q(is_active=False)
        ).order_by("-date", "-time_start")

        context = {
            "page_title": "Historiku",
            "page_subtitle": "Turet e kaluara dhe aktiviteti i kaluar i udhëzuesit.",
            "role": "guide",
            "history_items": history_items,
            "empty_message": "Nuk ka ende histori të tureve tuaja.",
        }
        return render(request, "users/activity_page.html", context)

    messages.error(request, "❌ Nuk ke akses në këtë faqe.")
    return redirect("core:home")


# ==================== PROFILE VIEWS ====================

class UserProfileDetailView(DetailView):
    """Shfaqja e profilit publik të guide-it"""
    
    model = GuideProfile
    template_name = "users/guide_profile_public.html"
    context_object_name = "guide"
    slug_field = "user__username"
    slug_url_kwarg = "username"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        guide = self.object

        # Tours
        context['tours'] = Tour.objects.filter(guide=guide, is_active=True).order_by('-date')[:6]

        # Reviews
        approved_reviews = TourReview.objects.filter(
            tour__guide=guide,
            is_approved=True
        )
        context['reviews'] = approved_reviews.select_related(
            'tourist__user', 'tour'
        ).order_by('-created_at')[:6]

        context['featured_reviews'] = approved_reviews.filter(
            is_featured=True
        ).select_related('tourist__user', 'tour').order_by('-created_at')[:3]

        context['avg_rating'] = approved_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        context['reviews_count'] = approved_reviews.count()

        # Shpërndarja e notave (5 -> 1) me përqindje për grafikun
        dist_raw = {
            d['rating']: d['count']
            for d in approved_reviews.values('rating').annotate(count=Count('id'))
        }
        total_ratings = sum(dist_raw.values()) or 1
        context['rating_distribution'] = [
            {
                'rating': star,
                'count': dist_raw.get(star, 0),
                'percentage': round((dist_raw.get(star, 0) / total_ratings) * 100, 1),
            }
            for star in range(5, 0, -1)
        ]

        # Detajet e vlerësimeve
        detail_agg = approved_reviews.aggregate(
            avg_guide=Avg('guide_rating'),
            avg_value=Avg('value_rating'),
            avg_experience=Avg('experience_rating'),
        )
        context['detail_ratings'] = {
            'guide': detail_agg['avg_guide'],
            'value': detail_agg['avg_value'],
            'experience': detail_agg['avg_experience'],
        }

        return context