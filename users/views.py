from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from .forms import SignupForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import GuideProfile, TouristProfile
from .forms import GuideProfileForm
from django.db.models import Sum, Count
from tours.models import Tour
from bookings.models import Booking
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse_lazy


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get("role")

            # Krijo profilin manualisht këtu – më e sigurt se me signal
            if role == "guide":
                GuideProfile.objects.create(
                    user=user
                )  # krijohet bosh, pastaj plotësohet
            else:
                TouristProfile.objects.create(user=user)

            # Login automatik
            login(request, user)

            messages.success(
                request, f"Mirëseerdhët {user.first_name}! Llogaria u krijua me sukses."
            )

            if role == "guide":
                messages.info(
                    request,
                    "Tani plotëso profilin tënd si Guide për të filluar të ofrosh ture!",
                )
                return redirect("users:guide_profile_edit")
            else:
                messages.info(request, "Mirëseerdhët! Paneli juaj është gati.")
                return redirect("users:tourist_dashboard")

    else:
        form = SignupForm()

    return render(request, "users/signup.html", {"form": form})


@login_required
def guide_profile_edit(request):
    try:
        profile = request.user.guide_profile
    except GuideProfile.DoesNotExist:
        messages.error(request, "Nuk ke akses në këtë faqe. Duhet të jesh Guide.")
        return redirect("home")

    if request.method == "POST":
        form = GuideProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profili yt u përditësua me sukses!")
            return redirect("users:guide_dashboard")
        # Nëse form nuk është valid → vazhdo më poshtë me të njëjtën form (me gabime)
    else:
        # GET request → krijo formën bosh (me të dhënat aktuale)
        form = GuideProfileForm(instance=profile)

    return render(
        request, "users/guide_profile_edit.html", {"form": form, "profile": profile}
    )


@login_required
def guide_dashboard(request):
    # Kontrollo nëse përdoruesi është Guide
    try:
        guide_profile = request.user.guide_profile
    except:
        messages.error(request, "Kjo faqe është vetëm për guidat.")
        return redirect("tours:tour_list")

    # Merr të gjitha ture të kësaj guide
    tours = Tour.objects.filter(guide=guide_profile).order_by("-date")

    # Merr të gjitha rezervimet për ture të kësaj guide
    bookings = (
        Booking.objects.filter(tour__guide=guide_profile)
        .select_related("tour", "tourist__user")
        .order_by("-created_at")
    )

    # Statistika
    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status="pending").count()
    confirmed_bookings = bookings.filter(status="confirmed").count()

    # Të ardhura totale të pritshme (vetëm nga rezervimet e konfirmuara)
    revenue = (
        bookings.filter(status="confirmed").aggregate(total=Sum("total_price"))["total"]
        or 0
    )

    context = {
        "guide_profile": guide_profile,
        "tours": tours,
        "bookings": bookings,
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "confirmed_bookings": confirmed_bookings,
        "revenue": revenue,
    }

    return render(request, "users/guide_dashboard.html", context)


@login_required
def booking_action(request, booking_id, action):
    # Vetëm guida e turit mund të veprojë
    booking = get_object_or_404(Booking, id=booking_id)

    if (
        not hasattr(request.user, "guide_profile")
        or booking.tour.guide != request.user.guide_profile
    ):
        messages.error(request, "Nuk ke leje për këtë veprim.")
        return redirect("users:guide_dashboard")

    tourist_email = booking.tourist.user.email

    if action == "confirm":
        booking.status = "confirmed"
        booking.save()
        messages.success(
            request,
            f"Rezervimi nga {booking.tourist.user.get_full_name()} u konfirmua!",
        )

        if tourist_email:
            subject = f"Rezervimi juaj për '{booking.tour.title}' u konfirmua!"
            message = render_to_string(
                "emails/booking_status_tourist.txt",
                {
                    "tourist_name": booking.tourist.user.get_full_name()
                    or booking.tourist.user.username,
                    "tour_title": booking.tour.title,
                    "tour_date": booking.tour.date,
                    "tour_time": booking.tour.time_start,
                    "num_people": booking.num_people,
                    "total_price": booking.total_price,
                    "guide_name": booking.tour.guide.user.get_full_name()
                    or booking.tour.guide.user.username,
                    "guide_phone": booking.tour.guide.phone,
                    "tour_location_start": booking.tour.location_start,
                    "status": "confirmed",
                    "status_display": "Konfirmuar",
                },
            )
            send_mail(subject, message, "no-reply@platforma-jone.com", [tourist_email])

    elif action == "cancel":
        booking.cancel()
        messages.success(request, f"Rezervimi u anulua dhe vendet u kthyen.")

        if tourist_email:
            subject = f"Rezervimi juaj për '{booking.tour.title}' u anulua"
            message = render_to_string(
                "emails/booking_status_tourist.txt",
                {
                    "tourist_name": booking.tourist.user.get_full_name()
                    or booking.tourist.user.username,
                    "tour_title": booking.tour.title,
                    "tour_date": booking.tour.date,
                    "tour_time": booking.tour.time_start,
                    "num_people": booking.num_people,
                    "total_price": booking.total_price,
                    "guide_name": booking.tour.guide.user.get_full_name()
                    or booking.tour.guide.user.username,
                    "guide_phone": booking.tour.guide.phone,
                    "tour_location_start": booking.tour.location_start,
                    "status": "cancelled",
                    "status_display": "Anulluar",
                },
            )
            send_mail(subject, message, "no-reply@platforma-jone.com", [tourist_email])

    return redirect("users:guide_dashboard")


@login_required
def tourist_dashboard(request):
    """Tourist panel for managing bookings and 24h confirmation."""
    try:
        tourist_profile = request.user.tourist_profile
    except TouristProfile.DoesNotExist:
        messages.error(request, "Kjo faqe është vetëm për turistët.")
        return redirect("home")

    # Get all bookings for this tourist, sorted by tour date
    bookings = (
        Booking.objects.filter(tourist=tourist_profile)
        .select_related("tour__guide__user")
        .order_by("-tour__date")
    )

    # Separate upcoming and past bookings
    now = timezone.now()
    upcoming_bookings = []
    past_bookings = []
    needs_confirmation = []

    for booking in bookings:
        tour_start = timezone.make_aware(
            timezone.datetime.combine(booking.tour.date, booking.tour.time_start)
        )
        if tour_start > now:
            upcoming_bookings.append(booking)
            # Check if needs 24h confirmation (within 24h and not confirmed)
            hours_until = (tour_start - now).total_seconds() / 3600
            if (
                hours_until <= 24
                and not booking.is_confirmed_24h
                and booking.status == "confirmed"
            ):
                needs_confirmation.append(booking)
        else:
            past_bookings.append(booking)

    # Stats
    total_bookings = bookings.count()
    confirmed_bookings = bookings.filter(status="confirmed").count()
    pending_bookings = bookings.filter(status="pending").count()
    total_spent = (
        bookings.filter(status="confirmed").aggregate(total=Sum("total_price"))["total"]
        or 0
    )

    context = {
        "tourist_profile": tourist_profile,
        "upcoming_bookings": upcoming_bookings,
        "past_bookings": past_bookings,
        "needs_confirmation": needs_confirmation,
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_bookings,
        "pending_bookings": pending_bookings,
        "total_spent": total_spent,
    }

    return render(request, "users/tourist_dashboard.html", context)


@login_required
def confirm_participation(request, booking_id):
    """Tourist confirms participation in tour 24h before start."""
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.tourist.user != request.user:
        messages.error(request, "Nuk ke leje për këtë veprim.")
        return redirect("users:tourist_dashboard")

    if not booking.is_24h_before_tour():
        messages.error(
            request, "Mund të konfirmosh vetëm 24 orë përpara fillimit të turit."
        )
        return redirect("users:tourist_dashboard")

    booking.is_confirmed_24h = True
    booking.confirmed_24h_at = timezone.now()
    booking.save(update_fields=["is_confirmed_24h", "confirmed_24h_at"])

    messages.success(
        request,
        f"Faleminderit! Pjesmarrja jote në '{booking.tour.title}' u konfirmua.",
    )
    return redirect("users:tourist_dashboard")


@login_required
def cancel_booking(request, booking_id):
    """Tourist cancels their booking."""
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.tourist.user != request.user:
        messages.error(request, "Nuk ke leje për këtë veprim.")
        return redirect("users:tourist_dashboard")

    if booking.status == "cancelled":
        messages.info(request, "Ky rezervim është tashmë anulluar.")
        return redirect("users:tourist_dashboard")

    booking.cancel()
    messages.success(request, f"Rezervimi për '{booking.tour.title}' u anullua.")
    return redirect("users:tourist_dashboard")


class CustomLoginView(LoginView):
    """Custom login view that redirects tourists and guides to their respective dashboards."""

    template_name = "users/login.html"

    def get_success_url(self):
        """Redirect based on user role (tourist or guide)."""
        user = self.request.user

        # Check for guide profile first
        try:
            guide_profile = GuideProfile.objects.get(user=user)
            if guide_profile:
                return reverse_lazy("users:guide_dashboard")
        except GuideProfile.DoesNotExist:
            pass

        # Check for tourist profile
        try:
            tourist_profile = TouristProfile.objects.get(user=user)
            if tourist_profile:
                return reverse_lazy("users:tourist_dashboard")
        except TouristProfile.DoesNotExist:
            pass

        # Default redirect
        return reverse_lazy("home")
