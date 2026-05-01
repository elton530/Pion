from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Avg
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
            user = form.save()
            role = form.cleaned_data.get("role")
            
            # Profile creation is handled by the form's `save()` method.
            # Keep this view simple and avoid duplicating profile creation.
            
            # Login automatik
            login(request, user)
            
            messages.success(
                request,
                f"🎉 Mirëseerdhët {user.first_name}! Llogaria u krijua me sukses."
            )
            
            if role == "guide":
                messages.info(
                    request,
                    "📋 Tani plotëso profilin tënd si Guide për të filluar të ofrosh ture!"
                )
                return redirect("users:guide_profile_edit")
            else:
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
    tours = Tour.objects.filter(guide=guide_profile).order_by("-date")
    
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
    cancelled_bookings = bookings.filter(status="cancelled").count()
    
    # Të ardhura
    revenue = bookings.filter(status="confirmed").aggregate(
        total=Sum("total_price")
    )["total"] or 0
    
    # Vlerësime
    reviews = TourReview.objects.filter(
        tour__guide=guide_profile,
        is_approved=True
    )
    
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    
    context = {
        'guide_profile': guide_profile,
        'tours': tours,
        'page_obj': page_obj,
        'bookings': page_obj.object_list,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'revenue': revenue,
        'reviews_count': reviews.count(),
        'avg_rating': round(avg_rating, 1),
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
            booking.status = "confirmed"
            booking.confirmed_at = timezone.now()
            booking.save(update_fields=['status', 'confirmed_at'])
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
        context['reviews'] = TourReview.objects.filter(
            tour__guide=guide,
            is_approved=True
        ).order_by('-created_at')[:5]
        
        context['avg_rating'] = TourReview.objects.filter(
            tour__guide=guide,
            is_approved=True
        ).aggregate(avg=Avg('rating'))['avg'] or 0
        
        return context