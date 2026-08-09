from decimal import Decimal, InvalidOperation

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Booking, Payment, BookingReview


# ==================== BOOKING ADMIN ====================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin për prenime"""
    
    list_display = [
        'booking_info', 'tour_link', 'tourist_name', 'num_people_display',
        'price_display', 'status_badge', 'payment_status', 'created_at'
    ]
    
    list_filter = [
        'status', 'tour__date', 'tour__guide',
        'created_at', 'cancelled_by', 'is_confirmed_24h'
    ]
    
    search_fields = [
        'tour__title', 'tour__location_city',
        'tourist__user__first_name', 'tourist__user__last_name',
        'tourist__user__email', 'id'
    ]
    
    readonly_fields = [
        'id', 'price_per_person', 'total_price', 'final_price',
        'discount_applied', 'created_at', 'updated_at',
        'confirmed_at', 'cancelled_at', 'confirmed_24h_at',
        'tour_link', 'tourist_link', 'refund_info'
    ]
    
    fieldsets = (
        ('Informacioni Bazik', {
            'fields': ('id', 'tour_link', 'tourist_link')
        }),
        ('Pjesëmarrja', {
            'fields': ('num_people', 'participants_info')
        }),
        ('Çmimet', {
            'fields': (
                'price_per_person', 'total_price', 'discount_applied', 'final_price'
            )
        }),
        ('Statusi dhe Workflow', {
            'fields': (
                'status', 'confirmed_at', 'is_confirmed_24h', 'confirmed_24h_at'
            )
        }),
        ('Komunikim', {
            'fields': ('notes', 'special_requirements', 'guide_notes'),
            'classes': ('collapse',)
        }),
        ('Anulim', {
            'fields': (
                'cancelled_at', 'cancelled_by', 'cancellation_reason',
                'cancellation_notes', 'refund_info'
            ),
            'classes': ('collapse',)
        }),
        ('Kohë', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'confirm_bookings', 'cancel_bookings', 'mark_completed',
        'mark_no_show', 'send_confirmation_email'
    ]
    
    date_hierarchy = 'tour__date'
    ordering = ['-created_at']
    
    def booking_info(self, obj):
        """Informacioni i prenimit"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.tour.title,
            obj.id
        )
    booking_info.short_description = 'Prenim'
    
    def tour_link(self, obj):
        """Link drejt turit"""
        url = reverse('admin:tours_tour_change', args=[obj.tour.id])
        return format_html('<a href="{}">{}</a>', url, obj.tour.title)
    tour_link.short_description = 'Turi'
    
    def tourist_name(self, obj):
        """Emri i turistit"""
        return obj.tourist.user.get_full_name() or obj.tourist.user.username
    tourist_name.short_description = 'Turist'
    tourist_name.admin_order_field = 'tourist__user__first_name'
    
    def tourist_link(self, obj):
        """Link drejt turistit"""
        url = reverse('admin:auth_user_change', args=[obj.tourist.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.tourist.user.username)
    tourist_link.short_description = 'Turist'
    
    def num_people_display(self, obj):
        """Numri i personave me ikonë"""
        return format_html('👥 {}', obj.num_people)
    num_people_display.short_description = 'Persona'
    num_people_display.admin_order_field = 'num_people'
    
    def price_display(self, obj):
        """Çmimi final"""
        try:
            amount = Decimal(str(obj.final_price))
            amount_text = f"{amount:.2f}"
        except (InvalidOperation, TypeError, ValueError):
            amount_text = str(obj.final_price or "")
        return format_html(
            '💰 {} {}',
            amount_text,
            obj.tour.currency
        )
    price_display.short_description = 'Çmimi'
    price_display.admin_order_field = 'final_price'
    
    def status_badge(self, obj):
        """Statusi me badge"""
        colors = {
            'pending': '#f39c12',
            'confirmed': '#27ae60',
            'completed': '#3498db',
            'cancelled': '#e74c3c',
            'no_show': '#e67e22',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statusi'
    status_badge.admin_order_field = 'status'
    
    def payment_status(self, obj):
        """Statusi i pagesës"""
        try:
            payment = obj.payment
            colors = {
                'pending': '#f39c12',
                'paid': '#27ae60',
                'failed': '#e74c3c',
                'refunded': '#3498db',
            }
            color = colors.get(payment.status, '#95a5a6')
            icon = {'paid': '✅', 'pending': '⏳', 'failed': '❌', 'refunded': '↩️'}.get(payment.status, '?')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{} {}</span>',
                color, icon, payment.get_status_display()
            )
        except:
            return '—'
    payment_status.short_description = 'Pagesa'
    
    def refund_info(self, obj):
        """Informacioni i rimburses"""
        if obj.status == 'cancelled':
            try:
                refund_amount = Decimal(str(obj.refund_amount))
                refund_text = f"{refund_amount:.2f}"
            except (InvalidOperation, TypeError, ValueError):
                refund_text = str(obj.refund_amount or "")
            return format_html(
                '<span style="color: green; font-weight: bold;">↩️ Rimbursim: {} {}</span>',
                refund_text,
                obj.tour.currency
            )
        return '—'
    refund_info.short_description = 'Rimbursim'
    
    # ===== ACTIONS =====
    
    def confirm_bookings(self, request, queryset):
        """Konfirmim i prenimeve"""
        count = 0
        for booking in queryset:
            if booking.status == 'pending':
                booking.confirm()
                count += 1
        self.message_user(request, f'✅ {count} prenim(e) u konfirmuan.')
    confirm_bookings.short_description = '✅ Konfirmo prenomet e zgjedhura'
    
    def cancel_bookings(self, request, queryset):
        """Anulim i prenimeve"""
        count = 0
        for booking in queryset:
            if booking.status != 'cancelled':
                try:
                    booking.cancel(cancelled_by='admin')
                    count += 1
                except ValueError:
                    pass
        self.message_user(request, f'❌ {count} prenim(e) u anulluan dhe vendet u kthyen.')
    cancel_bookings.short_description = '❌ Anullo prenomet dhe kthe vendet'
    
    def mark_completed(self, request, queryset):
        """Marko si të përfunduar"""
        count = queryset.filter(status='confirmed').update(status='completed')
        self.message_user(request, f'✔️ {count} prenim(e) u shënua si të përfunduar.')
    mark_completed.short_description = '✔️ Marko si të përfunduar'
    
    def mark_no_show(self, request, queryset):
        """Marko si nuk u paraqit"""
        count = 0
        for booking in queryset:
            booking.mark_no_show()
            count += 1
        self.message_user(request, f'⚠️ {count} prenim(e) shënuet si nuk u paraqit.')
    mark_no_show.short_description = '⚠️ Marko si nuk u paraqit'
    
    def send_confirmation_email(self, request, queryset):
        """Dërgoni email confirmimi"""
        count = 0
        for booking in queryset:
            if booking.status == 'confirmed':
                try:
                    from .views import send_booking_confirmation_email_to_tourist
                    send_booking_confirmation_email_to_tourist(booking)
                    count += 1
                except:
                    pass
        self.message_user(request, f'📧 {count} email(a) u dërguan.')
    send_confirmation_email.short_description = '📧 Dërgoni email confirmimi'


# ==================== PAYMENT ADMIN ====================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin për pagesat"""
    
    list_display = [
        'id_display', 'booking_link', 'amount_display',
        'payment_method_display', 'status_badge', 'paid_at'
    ]
    
    list_filter = [
        'status', 'payment_method', 'created_at', 'paid_at'
    ]
    
    search_fields = [
        'booking__id', 'booking__tour__title',
        'booking__tourist__user__username', 'transaction_id'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'booking_link'
    ]
    
    fieldsets = (
        ('Informacioni Bazik', {
            'fields': ('id', 'booking_link', 'amount', 'currency')
        }),
        ('Detajet e Pagesës', {
            'fields': ('payment_method', 'status', 'transaction_id')
        }),
        ('Kohë', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
        ('Shënime', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_failed', 'mark_as_refunded']
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def id_display(self, obj):
        """Shfaq ID"""
        return str(obj.id)[:8] + '...'
    id_display.short_description = 'ID'
    
    def booking_link(self, obj):
        """Link drejt prenimit"""
        url = reverse('admin:bookings_booking_change', args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, obj.booking.tour.title)
    booking_link.short_description = 'Prenim'
    
    def amount_display(self, obj):
        """Shfaq shumën"""
        try:
            amount = Decimal(str(obj.amount))
            amount_text = f"{amount:.2f}"
        except (InvalidOperation, TypeError, ValueError):
            amount_text = str(obj.amount or "")
        return format_html(
            '💰 {} {}',
            amount_text,
            obj.currency
        )
    amount_display.short_description = 'Shuma'
    amount_display.admin_order_field = 'amount'
    
    def payment_method_display(self, obj):
        """Metoda e pagesës"""
        icons = {
            'card': '💳',
            'paypal': '🅿️',
            'bank_transfer': '🏦',
            'cash': '💵',
        }
        icon = icons.get(obj.payment_method, '?')
        return format_html('{} {}', icon, obj.get_payment_method_display())
    payment_method_display.short_description = 'Metoda'
    payment_method_display.admin_order_field = 'payment_method'
    
    def status_badge(self, obj):
        """Statusi me badge"""
        colors = {
            'pending': '#f39c12',
            'paid': '#27ae60',
            'failed': '#e74c3c',
            'refunded': '#3498db',
        }
        color = colors.get(obj.status, '#95a5a6')
        icons = {
            'pending': '⏳',
            'paid': '✅',
            'failed': '❌',
            'refunded': '↩️',
        }
        icon = icons.get(obj.status, '?')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = 'Statusi'
    status_badge.admin_order_field = 'status'
    
    # ===== ACTIONS =====
    
    def mark_as_paid(self, request, queryset):
        """Marko si paguar"""
        count = queryset.filter(status='pending').update(status='paid')
        self.message_user(request, f'✅ {count} pagesa u shënua si e paguar.')
    mark_as_paid.short_description = '✅ Marko si të paguara'
    
    def mark_as_failed(self, request, queryset):
        """Marko si dështuar"""
        count = queryset.filter(status='pending').update(status='failed')
        self.message_user(request, f'❌ {count} pagesa u shënua si dështuar.')
    mark_as_failed.short_description = '❌ Marko si dështuar'
    
    def mark_as_refunded(self, request, queryset):
        """Marko si kthyer"""
        count = queryset.filter(status='paid').update(status='refunded')
        self.message_user(request, f'↩️ {count} pagesa u shënua si kthyer.')
    mark_as_refunded.short_description = '↩️ Marko si të kthyera'


# ==================== BOOKING REVIEW ADMIN ====================

@admin.register(BookingReview)
class BookingReviewAdmin(admin.ModelAdmin):
    """Admin për vlerësimet e prenimeve"""
    
    list_display = [
        'booking_link', 'tourist_name', 'rating_display', 'created_at'
    ]
    
    list_filter = ['rating', 'created_at']
    
    search_fields = [
        'booking__id', 'booking__tour__title',
        'booking__tourist__user__username'
    ]
    
    readonly_fields = ['created_at', 'booking_link']
    
    fieldsets = (
        ('Informacioni Bazik', {
            'fields': ('booking_link', 'rating')
        }),
        ('Vlerësimi', {
            'fields': ('comment',)
        }),
        ('Kohë', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def booking_link(self, obj):
        """Link drejt prenimit"""
        url = reverse('admin:bookings_booking_change', args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, obj.booking.tour.title)
    booking_link.short_description = 'Prenim'
    
    def tourist_name(self, obj):
        """Emri i turistit"""
        return obj.booking.tourist.user.get_full_name() or obj.booking.tourist.user.username
    tourist_name.short_description = 'Turist'
    
    def rating_display(self, obj):
        """Vlerësimi me yje"""
        stars = '⭐' * obj.rating
        return format_html('{} {}/5', stars, obj.rating)
    rating_display.short_description = 'Vlerësim'
    rating_display.admin_order_field = 'rating'