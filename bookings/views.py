from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tours.models import Tour
from users.models import TouristProfile
from .forms import BookingForm
from .models import Booking
from django.core.mail import send_mail
from django.template.loader import render_to_string


@login_required
def create_booking(request, slug):
    tour = get_object_or_404(Tour, slug=slug, is_active=True)

    # Kontrollo nëse përdoruesi është Tourist
    try:
        tourist_profile = request.user.tourist_profile
    except TouristProfile.DoesNotExist:
        messages.error(request, "Vetëm turistët mund të rezervojnë ture.")
        return redirect("tours:tour_detail", slug=tour.slug)

    # Kontrollo nëse ka rezervuar tashmë
    if Booking.objects.filter(tourist=tourist_profile, tour=tour).exists():
        messages.info(request, "Ke tashmë një rezervim për këtë tur.")
        return redirect("tours:tour_detail", slug=tour.slug)

    if tour.available_spots <= 0:
        messages.error(request, "Kujdes! Nuk ka më vende të lira për këtë tur.")
        return redirect("tours:tour_detail", slug=tour.slug)

    if request.method == "POST":
        form = BookingForm(request.POST, tour=tour, tourist=tourist_profile)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.tour = tour
            booking.tourist = tourist_profile
            booking.save()

        # Dërgo email te guida

        guide_email = tour.guide.user.email
        if guide_email:
            subject = f"Rezervim i ri për turin '{tour.title}'"
            message = render_to_string(
                "emails/new_booking_guide.txt",
                {
                    "guide_name": tour.guide.user.get_full_name()
                    or tour.guide.user.username,
                    "tour_title": tour.title,
                    "tour_date": tour.date,
                    "tour_time": tour.time_start,
                    "tourist_name": booking.tourist.user.get_full_name()
                    or booking.tourist.user.username,
                    "tourist_phone": booking.tourist.phone,
                    "num_people": booking.num_people,
                    "total_price": booking.total_price,
                    "notes": booking.notes,
                },
            )
            send_mail(subject, message, "no-reply@platforma-jone.com", [guide_email])

        messages.success(
            request,
            f'Rezervimi për "{tour.title}" u krye me sukses! Presim konfirmimin nga guida.',
        )
        return redirect("bookings:booking_success", slug=tour.slug)
    else:
        form = BookingForm(tour=tour, tourist=tourist_profile)

    return render(
        request,
        "bookings/create_booking.html",
        {
            "form": form,
            "tour": tour,
        },
    )


def booking_success(request, slug):
    tour = get_object_or_404(Tour, slug=slug)
    return render(request, "bookings/booking_success.html", {"tour": tour})


# Create your views here.
