from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, ListView
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from decimal import Decimal

from tours.models import Tour
from users.models import TouristProfile, GuideProfile
from .forms import (
    BookingForm, BookingEditForm, BookingCancellationForm,
    BookingConfirmationForm, BookingReviewForm, BookingSearchForm
)
from .models import Booking, Payment, BookingReview


# ==================== BOOKING CREATION ====================

@login_required
def create_booking(request, slug):
    """Krijim i një prenim të ri"""
    
    tour = get_object_or_404(Tour, slug=slug, is_active=True, status="published")
    
    # Kontrollo nëse përdoruesi është turist
    try:
        tourist_profile = request.user.tourist_profile
    except TouristProfile.DoesNotExist:
        messages.error(request, "❌ Vetëm turistët mund të rezervojnë ture.")
        return redirect("tours:tour_detail", slug=tour.slug)
    
    # Kontrollo disponibilitetin e turit
    if not tour.can_be_booked:
        messages.error(request, "❌ Ky tur nuk është më i disponueshëm për prenim.")
        return redirect("tours:tour_detail", slug=tour.slug)
    
    # Kontrollo nëse ka tashmë prenim
    existing = Booking.objects.filter(
        tourist=tourist_profile,
        tour=tour
    ).exclude(status='cancelled').first()
    
    if existing:
        messages.info(
            request,
            f"ℹ️ Ke tashmë një prenim për këtë tur me status '{existing.get_status_display()}'."
        )
        return redirect("users:tourist_booking_detail", booking_id=existing.id)
    
    if request.method == "POST":
        form = BookingForm(request.POST, tour=tour, tourist=tourist_profile)
        
        if form.is_valid():
            # Guard: ensure tour.current_price is numeric before creating Booking
            try:
                Decimal(str(tour.current_price))
            except Exception:
                messages.error(request, "❌ Nuk mund të vazhdosh - çmimi i turit nuk është i vlefshëm. Kontakto administratën.")
                return redirect("tours:tour_detail", slug=tour.slug)

            try:
                booking = form.save(commit=False)
                booking.tour = tour
                booking.tourist = tourist_profile
                booking.save()
                
                # Dërgoni email tek guide-i
                send_new_booking_email_to_guide(booking)
                
                # Dërgoni email tek turist
                send_booking_confirmation_email_to_tourist(booking)
                
                messages.success(
                    request,
                    f'✅ Rezervimi për "{tour.title}" u krye me sukses! Presim konfirmimin nga guida.'
                )
                return redirect("bookings:booking_success", booking_id=booking.id)
            
            except ValueError as e:
                messages.error(request, f"❌ {str(e)}")
                return redirect("tours:tour_detail", slug=tour.slug)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    else:
        form = BookingForm(tour=tour, tourist=tourist_profile)
    
    context = {
        'form': form,
        'tour': tour,
        'available_spots': tour.available_spots,
    }
    
    return render(request, "bookings/create_booking.html", context)


@login_required
def booking_success(request, booking_id):
    """Faqja e suksesit pas prenimit"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tourist.user != request.user:
        raise PermissionDenied("Nuk ke leje për këtë faqe.")
    
    context = {
        'booking': booking,
        'tour': booking.tour,
    }
    
    return render(request, "bookings/booking_success.html", context)


# ==================== BOOKING MANAGEMENT ====================

@login_required
def booking_detail(request, booking_id):
    """Detajet e një prenimit"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Kontrollo autorizimin (turist ose guide)
    is_tourist = booking.tourist.user == request.user
    is_guide = booking.tour.guide.user == request.user
    
    if not (is_tourist or is_guide):
        raise PermissionDenied("Nuk ke leje për të parë këtë prenim.")
    
    context = {
        'booking': booking,
        'is_tourist': is_tourist,
        'is_guide': is_guide,
        'can_cancel': booking.can_be_cancelled,
        'refund_amount': booking.refund_amount,
    }
    
    return render(request, "bookings/booking_detail.html", context)


@login_required
def booking_edit(request, booking_id):
    """Redaktim i prenimit"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Vetëm turist mund të editoj
    if booking.tourist.user != request.user:
        raise PermissionDenied("Nuk ke leje për këtë veprim.")
    
    # Mund të editoj vetëm në pending status
    if booking.status != "pending":
        messages.error(request, "❌ Mund të editosh vetëm prenime në pritje.")
        return redirect("bookings:booking_detail", booking_id=booking.id)
    
    if request.method == "POST":
        form = BookingEditForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Prenimit u përditësua me sukses!")
            return redirect("bookings:booking_detail", booking_id=booking.id)
    else:
        form = BookingEditForm(instance=booking)
    
    context = {
        'form': form,
        'booking': booking,
    }
    
    return render(request, "bookings/booking_edit.html", context)


@login_required
def booking_cancel(request, booking_id):
    """Anulim i prenimit"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Vetëm turist mund të anuloj
    if booking.tourist.user != request.user:
        raise PermissionDenied("Nuk ke leje për këtë veprim.")
    
    if not booking.can_be_cancelled:
        messages.error(
            request,
            f"❌ Nuk mund ta anulohet këtë prenim. Turit i mbeten {booking.days_until_tour} ditë."
        )
        return redirect("bookings:booking_detail", booking_id=booking.id)
    
    if request.method == "POST":
        form = BookingCancellationForm(request.POST)
        if form.is_valid():
            try:
                reason = form.cleaned_data.get('cancellation_reason')
                notes = form.cleaned_data.get('notes', '')
                
                booking.cancel(reason=reason, cancelled_by='tourist', notes=notes)
                
                # Dërgoni email confirmim
                send_cancellation_email(booking)
                
                refund = booking.refund_amount
                messages.success(
                    request,
                    f"✅ Prenimit u anullua. Rimbursim i pritshëm: {refund} {booking.tour.currency}"
                )
                return redirect("users:tourist_dashboard")
            
            except ValueError as e:
                messages.error(request, f"❌ {str(e)}")
    
    else:
        form = BookingCancellationForm()
    
    context = {
        'form': form,
        'booking': booking,
        'refund_amount': booking.refund_amount,
    }
    
    return render(request, "bookings/booking_cancel.html", context)


@login_required
def booking_confirm_participation(request, booking_id):
    """Konfirmim i pjesëmarrjes 24h përpara"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tourist.user != request.user:
        raise PermissionDenied("Nuk ke leje për këtë veprim.")
    
    if booking.status != "confirmed":
        messages.error(request, "❌ Mund të konfirmosh vetëm prenime të konfirmuara.")
        return redirect("bookings:booking_detail", booking_id=booking.id)
    
    if request.method == "POST":
        form = BookingConfirmationForm(request.POST)
        if form.is_valid():
            try:
                booking.confirm_participation_24h()
                messages.success(
                    request,
                    f"✅ Faleminderit! Pjesmarrja jote u konfirmua për '{booking.tour.title}'."
                )
            except ValueError as e:
                messages.error(request, f"❌ {str(e)}")
            
            return redirect("bookings:booking_detail", booking_id=booking.id)
    
    else:
        form = BookingConfirmationForm()
    
    context = {
        'form': form,
        'booking': booking,
        'tour': booking.tour,
    }
    
    return render(request, "bookings/booking_confirm_participation.html", context)


# ==================== BOOKING SEARCH ====================

@login_required
def booking_list(request):
    """Lista e prenimeve (për turistin)"""
    
    try:
        tourist_profile = request.user.tourist_profile
    except TouristProfile.DoesNotExist:
        messages.error(request, "❌ Vetëm turistët mund të shikojnë prenomet e tyre.")
        return redirect("home")
    
    bookings = Booking.objects.filter(tourist=tourist_profile).select_related('tour__guide__user')
    
    # Filtrim dhe kërkimi
    form = BookingSearchForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            bookings = bookings.filter(
                Q(tour__title__icontains=search) |
                Q(tour__location_city__icontains=search)
            )
        
        if form.cleaned_data.get('status'):
            statuses = form.cleaned_data['status']
            bookings = bookings.filter(status__in=statuses)
        
        if form.cleaned_data.get('date_from'):
            bookings = bookings.filter(
                tour__date__gte=form.cleaned_data['date_from']
            )
        
        if form.cleaned_data.get('date_to'):
            bookings = bookings.filter(
                tour__date__lte=form.cleaned_data['date_to']
            )
        
        sort_by = form.cleaned_data.get('sort_by', '-created_at')
        if sort_by:
            bookings = bookings.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_bookings': Booking.objects.filter(tourist=tourist_profile).count(),
        'confirmed_bookings': Booking.objects.filter(
            tourist=tourist_profile,
            status='confirmed'
        ).count(),
    }
    
    return render(request, "bookings/booking_list.html", context)


# ==================== REVIEW ====================

@login_required
def create_booking_review(request, booking_id):
    """Krijo vlerësim për prenimin"""
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.tourist.user != request.user:
        raise PermissionDenied("Nuk ke leje për këtë veprim.")
    
    if booking.status != "completed":
        messages.error(request, "❌ Mund të vlerësosh vetëm turet e përfunduar.")
        return redirect("bookings:booking_detail", booking_id=booking.id)
    
    if hasattr(booking, 'booking_review'):
        messages.info(request, "ℹ️ Ke tashmë një vlerësim për këtë prenim.")
        return redirect("bookings:booking_detail", booking_id=booking.id)
    
    if request.method == "POST":
        form = BookingReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.save()
            
            messages.success(request, "✅ Vlerësimi u regjistrua. Faleminderit!")
            return redirect("bookings:booking_detail", booking_id=booking.id)
        else:
            # Surface form errors in flash messages for visibility
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        label = form.fields[field].label if field in form.fields else field
                        messages.error(request, f"{label}: {error}")
    
    else:
        form = BookingReviewForm()
    
    context = {
        'form': form,
        'booking': booking,
        'tour': booking.tour,
    }
    
    return render(request, "bookings/create_booking_review.html", context)


# ==================== EMAIL HELPERS ====================

def send_new_booking_email_to_guide(booking):
    """Dërgoni email te guide kur ka prenim të ri"""
    try:
        guide_email = booking.tour.guide.user.email
        if guide_email:
            subject = f"📬 Prenim i ri për turin '{booking.tour.title}'"
            context = {
                'guide_name': booking.tour.guide.user.get_full_name() or booking.tour.guide.user.username,
                'tour_title': booking.tour.title,
                'tour_date': booking.tour.date,
                'tour_time': booking.tour.time_start,
                'tour_location': booking.tour.location_city,
                'tourist_name': booking.tourist.user.get_full_name() or booking.tourist.user.username,
                'tourist_phone': booking.tourist.phone or 'Nuk u sigurua',
                'num_people': booking.num_people,
                'total_price': booking.total_price,
                'currency': booking.tour.currency,
                'notes': booking.notes or 'Nuk ka shënime',
            }
            # message = render_to_string('emails/new_booking_guide.html', context)
            message = f"Prenim i ri: {booking.tourist.user.get_full_name()} për {booking.num_people} persona"
            send_mail(subject, message, 'no-reply@platforma-jone.com', [guide_email])
    except Exception as e:
        print(f"Gabim në dërgimin e email për guide: {e}")


def send_booking_confirmation_email_to_tourist(booking):
    """Dërgoni email confirmim te turist"""
    try:
        tourist_email = booking.tourist.user.email
        if tourist_email:
            subject = f"✅ Prenimit për '{booking.tour.title}'"
            context = {
                'tourist_name': booking.tourist.user.get_full_name() or booking.tourist.user.username,
                'tour_title': booking.tour.title,
                'tour_date': booking.tour.date,
                'tour_time': booking.tour.time_start,
                'guide_name': booking.tour.guide.user.get_full_name() or booking.tour.guide.user.username,
                'num_people': booking.num_people,
                'total_price': booking.total_price,
                'currency': booking.tour.currency,
            }
            message = f"Prenimit u krye. Guide-i do të kontaktojë së shpejti."
            send_mail(subject, message, 'no-reply@platforma-jone.com', [tourist_email])
    except Exception as e:
        print(f"Gabim në dërgimin e email për turist: {e}")


def send_cancellation_email(booking):
    """Dërgoni email confirmim anulimi"""
    try:
        tourist_email = booking.tourist.user.email
        if tourist_email:
            subject = f"❌ Anulim i prenimit për '{booking.tour.title}'"
            message = f"Prenimit u anullua. Rimbursim: {booking.refund_amount} {booking.tour.currency}"
            send_mail(subject, message, 'no-reply@platforma-jone.com', [tourist_email])
    except Exception as e:
        print(f"Gabim në dërgimin e email anulimi: {e}")