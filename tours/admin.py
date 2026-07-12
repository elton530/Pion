from decimal import Decimal, InvalidOperation

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Tour, TourImage, TourReview, TourType, TourSchedule,
    TourFAQ, TourHighlight, TourTag, TourStatistic, TourReviewImage
)
from .forms import TourEditForm  # ADD THIS IMPORT


# ==================== INLINES ====================

class TourImageInline(admin.TabularInline):
    """Inline për imazhet shtesë të turit"""
    model = TourImage
    extra = 1
    fields = ['image', 'caption', 'order', 'is_primary']
    ordering = ['order']


class TourScheduleInline(admin.TabularInline):
    """Inline për programin ditor të turit"""
    model = TourSchedule
    extra = 1
    fields = ['day_number', 'title', 'start_time', 'end_time', 'order']
    ordering = ['day_number']


class TourFAQInline(admin.TabularInline):
    """Inline për pyetjet e shpeshta"""
    model = TourFAQ
    extra = 1
    fields = ['question', 'order', 'is_active']
    ordering = ['order']


class TourHighlightInline(admin.TabularInline):
    """Inline për pikat kryesore"""
    model = TourHighlight
    extra = 1
    fields = ['icon', 'title', 'description', 'order']
    ordering = ['order']


class TourReviewInline(admin.TabularInline):
    """Inline për vlerësimet"""
    model = TourReview
    extra = 0
    fields = ['tourist', 'rating', 'is_approved', 'is_featured', 'created_at']
    readonly_fields = ['tourist', 'rating', 'created_at']
    can_delete = False


# ==================== TOUR TYPE ADMIN ====================

@admin.register(TourType)
class TourTypeAdmin(admin.ModelAdmin):
    """Admin për kategoritë e tureve"""
    
    list_display = ['name', 'color_preview', 'tour_count', 'is_active', 'order']
    list_filter = ['is_active', 'order']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Informacioni Bazik', {
            'fields': ('name', 'description')
        }),
        ('Shfaqja', {
            'fields': ('icon', 'color', 'order')
        }),
        ('Statusi', {
            'fields': ('is_active',)
        }),
    )
    
    def color_preview(self, obj):
        """Shfaq preview të ngjyrës"""
        return format_html(
            '<div style="background-color: {}; width: 30px; height: 30px; border-radius: 5px;"></div>',
            obj.color
        )
    color_preview.short_description = 'Ngjyra'
    
    def tour_count(self, obj):
        """Numri i tureve në këtë kategori"""
        return obj.tour_count
    tour_count.short_description = 'Numri i Tureve'


# ==================== TOUR ADMIN ====================

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    """Admin i plotë për Turet"""
    
    # ADD THIS LINE - Tell admin to use TourEditForm
    form = TourEditForm
    
    list_display = [
        'title', 'guide_name', 'date', 'tour_type_display',
        'difficulty_display', 'price_display', 'booking_status',
        'confirmed_bookings_display', 'rating_display', 'status_badge', 'is_active'
    ]
    
    list_filter = [
        'status', 'tour_type', 'difficulty', 'age_group',
        'date', 'is_active', 'is_featured', 'transportation_included',
        'meal_included', 'accommodation_included'
    ]
    
    search_fields = [
        'title', 'full_description', 'guide__user__first_name',
        'guide__user__last_name', 'location_city', 'location_region'
    ]
    
    readonly_fields = [
        'available_spots', 'booking_count', 'reviews_count',
        'average_rating', 'created_at', 'updated_at', 'last_booking_at',
        'booking_percentage_display'
    ]
    
    inlines = [
        TourImageInline, TourScheduleInline, TourFAQInline,
        TourHighlightInline, TourReviewInline
    ]
    
    prepopulated_fields = {"slug": ("title",)}
    
    fieldsets = (
        ('Informacioni Bazik', {
            'fields': ('guide', 'title', 'slug', 'status')
        }),
        ('Përshkrimet', {
            'fields': ('short_description', 'full_description'),
            'classes': ('collapse',)
        }),
        ('Kategorizimi', {
            'fields': ('tour_type', 'difficulty', 'age_group', 'languages')
        }),
        ('Lokacioni', {
            'fields': (
                'meeting_point', 'meeting_point_lat', 'meeting_point_lng',
                'location_city', 'location_region', 'end_point'
            ),
            'classes': ('collapse',)
        }),
        ('Kohëzgjatja', {
            'fields': ('date', 'time_start', 'time_end', 'duration_hours', 'duration_days')
        }),
        ('Detajet Fizike', {
            'fields': ('distance_km', 'elevation_gain', 'max_altitude'),
            'classes': ('collapse',)
        }),
        ('Çmimet', {
            'fields': (
                'price_per_person', 'currency', 'max_participants',
                'min_participants', 'available_spots', 'booking_percentage_display'
            )
        }),
        ('Zbritje', {
            'fields': (
                'has_discount', 'discount_price', 'discount_until',
                'early_bird_days', 'early_bird_discount'
            ),
            'classes': ('collapse',)
        }),
        ('Imazhet', {
            'fields': ('main_image', 'thumbnail'),
            'classes': ('collapse',)
        }),
        ('Përmbajtja', {
            'fields': (
                'highlights', 'included', 'not_included', 'what_to_bring'
            ),
            'classes': ('collapse',)
        }),
        ('Kërkesat', {
            'fields': (
                'requirements', 'health_warnings', 'equipment_provided'
            ),
            'classes': ('collapse',)
        }),
        ('Logjistika', {
            'fields': (
                'transportation_included', 'transportation_details',
                'meal_included', 'meal_details',
                'accommodation_included', 'accommodation_details'
            ),
            'classes': ('collapse',)
        }),
        ('Politika Anulimi', {
            'fields': (
                'cancellation_deadline_hours', 'cancellation_policy', 'refund_percentage'
            ),
            'classes': ('collapse',)
        }),
        ('SEO & Marketing', {
            'fields': (
                'meta_title', 'meta_description', 'meta_keywords',
                'is_featured', 'featured_until'
            ),
            'classes': ('collapse',)
        }),
        ('Vlerësimet', {
            'fields': ('average_rating', 'reviews_count'),
            'classes': ('collapse',)
        }),
        ('Statistika', {
            'fields': (
                'booking_count', 'created_at', 'updated_at', 'last_booking_at'
            ),
            'classes': ('collapse',)
        }),
        ('Statusi', {
            'fields': ('is_active',)
        }),
    )
    
    actions = ['publish_tours', 'draft_tours', 'hide_tours', 'activate_tours', 'deactivate_tours']
    
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    def guide_name(self, obj):
        """Emri i guide-it"""
        return obj.guide.user.get_full_name() or obj.guide.user.username
    guide_name.short_description = 'Guide'
    guide_name.admin_order_field = 'guide__user__first_name'
    
    def tour_type_display(self, obj):
        """Lloji i turit me ngjyrë"""
        if obj.tour_type:
            color = obj.tour_type.color or '#95a5a6'
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
                color, obj.tour_type.name
            )
        return '—'
    tour_type_display.short_description = 'Lloji'
    tour_type_display.admin_order_field = 'tour_type'
    
    def difficulty_display(self, obj):
        """Vshtirësia me ikonë"""
        icons = {
            'very_easy': '🟢',
            'easy': '🟡',
            'moderate': '🟠',
            'hard': '🔴',
            'expert': '⚫',
        }
        icon = icons.get(obj.difficulty, '')
        return format_html('{} {}', icon, obj.get_difficulty_display())
    difficulty_display.short_description = 'Vshtirësia'
    difficulty_display.admin_order_field = 'difficulty'
    
    def price_display(self, obj):
        """Çmimi me valutë"""
        try:
            price = Decimal(str(obj.price_per_person))
            price_text = f"{price:.2f}"
        except (InvalidOperation, TypeError, ValueError):
            price_text = str(obj.price_per_person or "")
        return format_html(
            '{} {}',
            price_text,
            obj.get_currency_display()
        )
    price_display.short_description = 'Çmimi'
    price_display.admin_order_field = 'price_per_person'
    
    def booking_status(self, obj):
        """Statusi i prenotazioneve"""
        try:
            percentage = Decimal(str(obj.confirmed_percentage))
            percentage_text = f"{percentage:.0f}"
        except (InvalidOperation, TypeError, ValueError):
            percentage = Decimal('0')
            percentage_text = '0'

        if percentage == 0:
            color = '#27ae60'  # green
            status = 'Bosh'
        elif percentage < 50:
            color = '#f39c12'  # orange
            status = 'Të Lira'
        elif percentage < 100:
            color = '#e67e22'  # dark orange
            status = 'Pak'
        else:
            color = '#e74c3c'  # red
            status = 'Plotë'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{} ({}%)</span>',
            color, status, percentage_text
        )
    booking_status.short_description = 'Statusi'
    
    def confirmed_bookings_display(self, obj):
        """Numri i prenotimeve të konfirmuara"""
        return format_html(
            '<span style="font-weight: bold;">{}</span> / {}',
            obj.booking_count, obj.max_participants
        )
    confirmed_bookings_display.short_description = 'Konfirmuar'
    
    def booking_percentage_display(self, obj):
        """Përqindja grafike e prenotazioneve"""
        try:
            percentage = Decimal(str(obj.booking_percentage))
            percentage_text = f"{percentage:.1f}"
        except (InvalidOperation, TypeError, ValueError):
            percentage = Decimal('0')
            percentage_text = '0.0'
        return format_html(
            '<div style="width: 200px; height: 20px; background-color: #ecf0f1; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; height: 100%; background-color: #3498db;"></div>'
            '</div> {}% ({}/{})',
            percentage, percentage_text, obj.max_participants - obj.available_spots, obj.max_participants
        )
    booking_percentage_display.short_description = 'Përqindja e Prenotazioneve'
    
    def rating_display(self, obj):
        """Vlerësimi me yje"""
        try:
            average_rating = Decimal(str(obj.average_rating))
            rating_text = f"{average_rating:.1f}"
        except (InvalidOperation, TypeError, ValueError):
            average_rating = None
            rating_text = '0.0'

        if average_rating is None or average_rating == 0:
            return '—'

        stars = '⭐' * int(average_rating)
        return format_html(
            '{} {}/5 ({})',
            stars, rating_text, obj.reviews_count
        )
    rating_display.short_description = 'Vlerësimi'
    rating_display.admin_order_field = 'average_rating'
    
    def status_badge(self, obj):
        """Statusi me badge"""
        colors = {
            'draft': '#95a5a6',
            'published': '#27ae60',
            'hidden': '#e67e22',
            'cancelled': '#e74c3c',
            'completed': '#3498db',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statusi'
    status_badge.admin_order_field = 'status'
    
    # ===== ACTIONS =====
    
    def publish_tours(self, request, queryset):
        """Action për publikimin e tureve"""
        count = queryset.update(status='published')
        self.message_user(request, f'{count} tur u publikua me sukses.')
    publish_tours.short_description = '📤 Publiko turet e zgjedhura'
    
    def draft_tours(self, request, queryset):
        """Action për draft status"""
        count = queryset.update(status='draft')
        self.message_user(request, f'{count} tur u vendos në draft.')
    draft_tours.short_description = '📝 Vendos në draft'
    
    def hide_tours(self, request, queryset):
        """Action për fshehjen e tureve"""
        count = queryset.update(status='hidden')
        self.message_user(request, f'{count} tur u fsheu.')
    hide_tours.short_description = '🙈 Fshih turet'
    
    def activate_tours(self, request, queryset):
        """Action për aktivizimin"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} tur u aktivizua.')
    activate_tours.short_description = '✅ Aktivizo turet'
    
    def deactivate_tours(self, request, queryset):
        """Action për deaktivizimin"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} tur u deaktivizua.')
    deactivate_tours.short_description = '❌ Deaktivizo turet'


# ==================== TOUR IMAGE ADMIN ====================

@admin.register(TourImage)
class TourImageAdmin(admin.ModelAdmin):
    """Admin për imazhet e tureve"""
    
    list_display = ['tour', 'image_preview', 'caption', 'order', 'is_primary']
    list_filter = ['tour', 'is_primary', 'created_at']
    search_fields = ['tour__title', 'caption']
    ordering = ['tour', 'order']
    
    fieldsets = (
        ('Informacioni', {
            'fields': ('tour', 'image', 'caption')
        }),
        ('Konfigurimi', {
            'fields': ('order', 'is_primary')
        }),
    )
    
    def image_preview(self, obj):
        """Preview i fotos"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 5px;" />',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Foto'


# ==================== TOUR REVIEW ADMIN ====================

@admin.register(TourReview)
class TourReviewAdmin(admin.ModelAdmin):
    """Admin për vlerësimet"""
    
    list_display = [
        'tourist_name', 'tour', 'rating_display', 'guide_rating',
        'value_rating', 'experience_rating', 'is_approved',
        'is_featured', 'is_verified', 'created_at'
    ]
    
    list_filter = [
        'rating', 'is_approved', 'is_featured', 'is_verified',
        'created_at', 'tour__difficulty'
    ]
    
    search_fields = [
        'tourist__user__first_name', 'tourist__user__last_name',
        'tour__title', 'comment'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'helpful_count']
    
    fieldsets = (
        ('Informacioni Bazik', {
            'fields': ('tour', 'tourist')
        }),
        ('Vlerësimet', {
            'fields': ('rating', 'guide_rating', 'value_rating', 'experience_rating', 'title')
        }),
        ('Komentimi', {
            'fields': ('comment', 'helpful_count')
        }),
        ('Admin', {
            'fields': ('is_approved', 'is_featured', 'is_verified')
        }),
        ('Timestamp-e', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reviews', 'reject_reviews', 'mark_as_featured', 'mark_as_verified']
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def tourist_name(self, obj):
        return obj.tourist.user.get_full_name() or obj.tourist.user.username
    tourist_name.short_description = 'Turist'
    tourist_name.admin_order_field = 'tourist__user__first_name'
    
    def rating_display(self, obj):
        """Vlerësimi me yje"""
        return format_html(
            '{}',
            '⭐' * obj.rating
        )
    rating_display.short_description = 'Vlerësim'
    rating_display.admin_order_field = 'rating'
    
    # ===== ACTIONS =====
    
    def approve_reviews(self, request, queryset):
        count = queryset.update(is_approved=True)
        self.message_user(request, f'{count} vlerësim u aprova.')
    approve_reviews.short_description = '✅ Aprovo vlerësimet'
    
    def reject_reviews(self, request, queryset):
        count = queryset.update(is_approved=False)
        self.message_user(request, f'{count} vlerësim u refuzua.')
    reject_reviews.short_description = '❌ Refuzo vlerësimet'
    
    def mark_as_featured(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f'{count} vlerësim u shënoj si featured.')
    mark_as_featured.short_description = '⭐ Shënoj si featured'
    
    def mark_as_verified(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} vlerësim u verifikua.')
    mark_as_verified.short_description = '✔️ Verifikoi vlerësimet'


# ==================== TOUR SCHEDULE ADMIN ====================

@admin.register(TourSchedule)
class TourScheduleAdmin(admin.ModelAdmin):
    """Admin për programet ditorë"""
    
    list_display = ['tour', 'day_number', 'title', 'start_time', 'end_time', 'order']
    list_filter = ['tour', 'day_number']
    search_fields = ['tour__title', 'title', 'description']
    ordering = ['tour', 'day_number']
    
    fieldsets = (
        ('Informacioni', {
            'fields': ('tour', 'day_number', 'title', 'order')
        }),
        ('Përshkrimi', {
            'fields': ('description',)
        }),
        ('Kohët', {
            'fields': ('start_time', 'end_time')
        }),
        ('Detajet', {
            'fields': ('meals_included', 'accommodation')
        }),
    )


# ==================== TOUR FAQ ADMIN ====================

@admin.register(TourFAQ)
class TourFAQAdmin(admin.ModelAdmin):
    """Admin për pyetjet e shpeshta"""
    
    list_display = ['tour', 'question', 'order', 'is_active']
    list_filter = ['tour', 'is_active']
    search_fields = ['tour__title', 'question', 'answer']
    ordering = ['tour', 'order']
    
    fieldsets = (
        ('Informacioni', {
            'fields': ('tour', 'question', 'order', 'is_active')
        }),
        ('Përgjigja', {
            'fields': ('answer',)
        }),
    )


# ==================== TOUR TAG ADMIN ====================

@admin.register(TourReviewImage)
class TourReviewImageAdmin(admin.ModelAdmin):
    """Admin për imazhet e vlerësimeve"""
    
    list_display = ['review', 'image_preview', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['review__tourist__user__first_name', 'review__tourist__user__last_name']
    readonly_fields = ['image_preview', 'uploaded_at']
    
    fieldsets = (
        ('Informacioni', {
            'fields': ('review',)
        }),
        ('Imazhi', {
            'fields': ('image', 'image_preview')
        }),
        ('Timestamp', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """Paraqitje e imazhit"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 4px;" />',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Paraqitje'


# ==================== TOUR HIGHLIGHT ADMIN ====================

@admin.register(TourHighlight)
class TourHighlightAdmin(admin.ModelAdmin):
    """Admin për pikat kryesore"""
    
    list_display = ['tour', 'icon', 'title', 'order']
    list_filter = ['tour']
    search_fields = ['tour__title', 'title', 'description']
    ordering = ['tour', 'order']
    
    fieldsets = (
        ('Informacioni', {
            'fields': ('tour', 'icon', 'title', 'order')
        }),
        ('Përshkrimi', {
            'fields': ('description',)
        }),
    )


# ==================== TOUR TAG ADMIN ====================

@admin.register(TourTag)
class TourTagAdmin(admin.ModelAdmin):
    """Admin për etiketat"""
    
    list_display = ['name', 'slug', 'tour_count']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    
    def tour_count(self, obj):
        return obj.tours.count()
    tour_count.short_description = 'Numri i Tureve'


# ==================== TOUR STATISTIC ADMIN ===================="

@admin.register(TourStatistic)
class TourStatisticAdmin(admin.ModelAdmin):
    """Admin për statistikat"""
    
    list_display = ['tour', 'views', 'unique_views', 'shares', 'inquiries', 'last_viewed']
    list_filter = ['created_at', 'last_viewed']
    search_fields = ['tour__title']
    readonly_fields = ['tour', 'views', 'unique_views', 'shares', 'inquiries', 'last_viewed', 'created_at']
    
    fieldsets = (
        ('Turi', {
            'fields': ('tour',)
        }),
        ('Statistika', {
            'fields': ('views', 'unique_views', 'shares', 'inquiries')
        }),
        ('Timestamp', {
            'fields': ('last_viewed', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    can_delete = False