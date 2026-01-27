from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import GuideProfile, TouristProfile


# ==================== GUIDE PROFILE ADMIN ====================

@admin.register(GuideProfile)
class GuideProfileAdmin(admin.ModelAdmin):
    """Admin për profilin e guide-it"""
    
    list_display = [
        'full_name', 'location', 'specialty_display', 'status_badge',
        'is_verified', 'rating_display', 'tours_count', 'created_at'
    ]
    
    list_filter = [
        'status', 'is_verified', 'is_active', 'experience_level',
        'specialty', 'created_at', 'verified_at'
    ]
    
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'location', 'languages', 'certifications'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at', 'verified_at', 'average_rating',
        'reviews_count', 'total_tours', 'total_tourists', 'total_earnings',
        'photo_preview', 'user_link'
    ]
    
    fieldsets = (
        ('Informacioni i Përdoruesit', {
            'fields': ('user_link', 'user',)
        }),
        ('Informacioni Personal', {
            'fields': ('photo', 'photo_preview', 'bio', 'phone', 'location')
        }),
        ('Informacioni Profesional', {
            'fields': (
                'specialty', 'specialties', 'experience_level', 'years_experience',
                'languages', 'certifications', 'certification_document'
            ),
            'classes': ('collapse',)
        }),
        ('Kontaktet Shoqëror', {
            'fields': ('website', 'instagram', 'facebook'),
            'classes': ('collapse',)
        }),
        ('Verifikimi', {
            'fields': (
                'status', 'is_verified', 'verified_at',
                'email_verified', 'phone_verified'
            )
        }),
        ('Vlerësimet dhe Statistika', {
            'fields': (
                'average_rating', 'reviews_count', 'total_tours',
                'total_tourists', 'total_earnings'
            ),
            'classes': ('collapse',)
        }),
        ('Statusi', {
            'fields': ('is_active',)
        }),
        ('Kohë', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'verify_guides', 'reject_guides', 'activate_guides',
        'deactivate_guides', 'mark_email_verified', 'mark_phone_verified'
    ]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def full_name(self, obj):
        """Emri i plotë i guide-it"""
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Emri'
    full_name.admin_order_field = 'user__first_name'
    
    def user_link(self, obj):
        """Link drejt përdoruesit"""
        from django.contrib.auth.models import User
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Përdoruesi'
    
    def specialty_display(self, obj):
        """Specialiteti me ngjyrë"""
        colors = {
            'nature_walk': '#27ae60',
            'alpine': '#2c3e50',
            'bike_tour': '#e74c3c',
            'cultural': '#f39c12',
            'adventure': '#9b59b6',
            'food': '#e67e22',
        }
        color = colors.get(obj.specialty, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_specialty_display()
        )
    specialty_display.short_description = 'Specialiteti'
    specialty_display.admin_order_field = 'specialty'
    
    def status_badge(self, obj):
        """Statusi me badge"""
        colors = {
            'pending': '#f39c12',
            'verified': '#27ae60',
            'rejected': '#e74c3c',
            'suspended': '#e67e22',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statusi'
    status_badge.admin_order_field = 'status'
    
    def rating_display(self, obj):
        """Vlerësimi me yje"""
        if obj.average_rating == 0:
            return '—'
        stars = '⭐' * int(obj.average_rating)
        return format_html(
            '{} {:.1f}/5 ({})',
            stars, obj.average_rating, obj.reviews_count
        )
    rating_display.short_description = 'Vlerësimi'
    rating_display.admin_order_field = 'average_rating'
    
    def tours_count(self, obj):
        """Numri i tureve"""
        return obj.total_tours
    tours_count.short_description = 'Turet'
    tours_count.admin_order_field = 'total_tours'
    
    def photo_preview(self, obj):
        """Preview i fotos"""
        if obj.photo:
            return format_html(
                '<img src="{}" width="100" height="100" style="border-radius: 5px;" />',
                obj.photo.url
            )
        return '—'
    photo_preview.short_description = 'Foto'
    
    # ===== ACTIONS =====
    
    def verify_guides(self, request, queryset):
        """Action për verifikimin e guide-ve"""
        count = queryset.update(status='verified', is_verified=True)
        self.message_user(request, f'✅ {count} guide u verifikuan.')
    verify_guides.short_description = '✅ Verifikoje guide-t e zgjedhura'
    
    def reject_guides(self, request, queryset):
        """Action për refuzimin e guide-ve"""
        count = queryset.update(status='rejected', is_verified=False)
        self.message_user(request, f'❌ {count} guide u refuzuan.')
    reject_guides.short_description = '❌ Refuzo guide-t e zgjedhura'
    
    def activate_guides(self, request, queryset):
        """Action për aktivizimin"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'✅ {count} guide u aktivizuan.')
    activate_guides.short_description = '✅ Aktivizo guide-t'
    
    def deactivate_guides(self, request, queryset):
        """Action për deaktivizimin"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'❌ {count} guide u deaktivizuan.')
    deactivate_guides.short_description = '❌ Deaktivizo guide-t'
    
    def mark_email_verified(self, request, queryset):
        """Action për verifikimin e email-it"""
        count = queryset.update(email_verified=True)
        self.message_user(request, f'✅ {count} email u verifikuan.')
    mark_email_verified.short_description = '✉️ Markoji email-at si të verifikuara'
    
    def mark_phone_verified(self, request, queryset):
        """Action për verifikimin e telefonit"""
        count = queryset.update(phone_verified=True)
        self.message_user(request, f'✅ {count} telefona u verifikuan.')
    mark_phone_verified.short_description = '📱 Markoji telefonat si të verifikuara'


# ==================== TOURIST PROFILE ADMIN ====================

@admin.register(TouristProfile)
class TouristProfileAdmin(admin.ModelAdmin):
    """Admin për profilin e turistit"""
    
    list_display = [
        'full_name', 'country', 'email_verified', 'phone_verified',
        'total_bookings', 'total_spent', 'created_at'
    ]
    
    list_filter = [
        'experience_level', 'email_verified', 'phone_verified',
        'email_notifications', 'sms_notifications', 'newsletter',
        'created_at'
    ]
    
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'user__email', 'country', 'phone'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at', 'total_bookings', 'total_spent',
        'photo_preview', 'user_link', 'age'
    ]
    
    fieldsets = (
        ('Informacioni i Përdoruesit', {
            'fields': ('user_link', 'user',)
        }),
        ('Informacioni Personal', {
            'fields': ('photo', 'photo_preview', 'bio', 'phone', 'age', 'date_of_birth', 'country')
        }),
        ('Preferencat', {
            'fields': (
                'experience_level', 'preferred_tour_types', 'languages'
            ),
            'classes': ('collapse',)
        }),
        ('Informacioni Shëndetësor', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone',
                'health_conditions', 'allergies'
            ),
            'classes': ('collapse',)
        }),
        ('Notifikime dhe Preferencat', {
            'fields': (
                'email_notifications', 'sms_notifications', 'newsletter'
            )
        }),
        ('Verifikimi', {
            'fields': ('email_verified', 'phone_verified')
        }),
        ('Statistika', {
            'fields': ('total_bookings', 'total_spent'),
            'classes': ('collapse',)
        }),
        ('Kohë', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_email_verified', 'mark_phone_verified',
        'enable_notifications', 'disable_notifications'
    ]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def full_name(self, obj):
        """Emri i plotë"""
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Emri'
    full_name.admin_order_field = 'user__first_name'
    
    def user_link(self, obj):
        """Link drejt përdoruesit"""
        from django.contrib.auth.models import User
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Përdoruesi'
    
    def age(self, obj):
        """Mosha e turistit"""
        return obj.age or '—'
    age.short_description = 'Mosha'
    
    def photo_preview(self, obj):
        """Preview i fotos"""
        if obj.photo:
            return format_html(
                '<img src="{}" width="100" height="100" style="border-radius: 5px;" />',
                obj.photo.url
            )
        return '—'
    photo_preview.short_description = 'Foto'
    
    # ===== ACTIONS =====
    
    def mark_email_verified(self, request, queryset):
        """Action për verifikimin e email-it"""
        count = queryset.update(email_verified=True)
        self.message_user(request, f'✅ {count} email u verifikuan.')
    mark_email_verified.short_description = '✉️ Markoji email-at si të verifikuara'
    
    def mark_phone_verified(self, request, queryset):
        """Action për verifikimin e telefonit"""
        count = queryset.update(phone_verified=True)
        self.message_user(request, f'✅ {count} telefona u verifikuan.')
    mark_phone_verified.short_description = '📱 Markoji telefonat si të verifikuara'
    
    def enable_notifications(self, request, queryset):
        """Action për aktivizimin e notifikimeve"""
        count = queryset.update(email_notifications=True)
        self.message_user(request, f'✅ {count} turistët marrin notifikime.')
    enable_notifications.short_description = '🔔 Aktivizo notifikime'
    
    def disable_notifications(self, request, queryset):
        """Action për deaktivizimin e notifikimeve"""
        count = queryset.update(email_notifications=False)
        self.message_user(request, f'🔕 {count} turistët nuk marrin notifikime.')
    disable_notifications.short_description = '🔕 Deaktivizo notifikime'