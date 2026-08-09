from django.contrib import admin
from django.utils.html import format_html

from .models import SiteSettings, ContactMessage, NewsletterSubscription, FAQ, SocialLink


# ==================== SITE SETTINGS ADMIN ====================

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin për konfigurimin e platformës"""
    
    list_display = ['site_name', 'maintenance_badge', 'contact_email', 'updated_at']
    
    fieldsets = (
        ('📱 Informacioni i Platformës', {
            'fields': ('site_name', 'site_description', 'site_logo', 'site_favicon')
        }),
        ('📧 Kontakti', {
            'fields': ('contact_email', 'contact_phone', 'contact_address')
        }),
        ('🔗 Rrjetet Shoqërore', {
            'fields': (
                'facebook_url', 'instagram_url', 'youtube_url',
                'tiktok_url', 'whatsapp_number'
            ),
            'classes': ('collapse',)
        }),
        ('⚖️ Aspekte Ligjore', {
            'fields': ('terms_and_conditions', 'privacy_policy'),
            'classes': ('collapse',)
        }),
        ('⚙️ Konfigurimi', {
            'fields': (
                'site_is_active', 'maintenance_mode', 'maintenance_message',
                'email_notifications_enabled', 'email_from_address'
            )
        }),
        ('🔍 SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('⏰ Kohë', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def maintenance_badge(self, obj):
        """Badge për statusin e mirëmbajtjes"""
        if obj.maintenance_mode:
            return format_html(
                '<span style="background-color: #f39c12; color: white; padding: 5px 10px; border-radius: 3px;">⚠️ Në mirëmbajtje</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 5px 10px; border-radius: 3px;">✅ Aktiv</span>'
            )
    maintenance_badge.short_description = 'Statusi'
    
    def has_add_permission(self, request):
        """Lejoj vetëm 1 instancë"""
        return False if SiteSettings.objects.exists() else True


# ==================== CONTACT MESSAGE ADMIN ====================

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Admin për mesazhe kontakti"""
    
    list_display = [
        'name_with_email', 'subject_display', 'status_badge',
        'replied_by_display', 'created_at'
    ]
    
    list_filter = [
        'status', 'created_at', 'replied_at'
    ]
    
    search_fields = [
        'name', 'email', 'subject', 'message', 'phone'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at', 'replied_at', 'message_display'
    ]
    
    fieldsets = (
        ('📋 Informacioni Bazik', {
            'fields': ('name', 'email', 'phone', 'subject')
        }),
        ('📝 Mesazhi', {
            'fields': ('message_display',)
        }),
        ('💬 Përgjigja', {
            'fields': ('reply_message', 'status', 'replied_by', 'replied_at'),
            'classes': ('collapse',)
        }),
        ('⏰ Kohë', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_replied', 'mark_as_resolved', 'mark_as_spam'
    ]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_select_related = ('replied_by',)
    
    def name_with_email(self, obj):
        """Emri me email"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.name,
            obj.email
        )
    name_with_email.short_description = 'Emri'
    
    def subject_display(self, obj):
        """Tema e shkurtuar"""
        return obj.subject[:50] + ('...' if len(obj.subject) > 50 else '')
    subject_display.short_description = 'Tema'
    
    def message_display(self, obj):
        """Shfaq mesazhin"""
        return obj.message
    message_display.short_description = 'Mesazhi'
    
    def status_badge(self, obj):
        """Status me badge"""
        colors = {
            'new': '#f39c12',
            'replied': '#27ae60',
            'resolved': '#3498db',
            'spam': '#e74c3c',
        }
        color = colors.get(obj.status, '#95a5a6')
        icons = {
            'new': '📬',
            'replied': '💬',
            'resolved': '✅',
            'spam': '⛔',
        }
        icon = icons.get(obj.status, '?')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = 'Statusi'
    status_badge.admin_order_field = 'status'
    
    def replied_by_display(self, obj):
        """Personi që përgjigjet"""
        if obj.replied_by:
            return obj.replied_by.get_full_name() or obj.replied_by.username
        return '—'
    replied_by_display.short_description = 'Përgjigjur nga'
    
    # ===== ACTIONS =====
    
    def mark_as_replied(self, request, queryset):
        """Marko si përgjigjur"""
        count = queryset.filter(status='new').update(status='replied')
        self.message_user(request, f'✅ {count} mesazh u shënua si përgjigjur.')
    mark_as_replied.short_description = '💬 Marko si përgjigjur'
    
    def mark_as_resolved(self, request, queryset):
        """Marko si zgjidhur"""
        count = queryset.update(status='resolved')
        self.message_user(request, f'✅ {count} mesazh u shënua si zgjidhur.')
    mark_as_resolved.short_description = '✅ Marko si zgjidhur'
    
    def mark_as_spam(self, request, queryset):
        """Marko si spam"""
        count = queryset.update(status='spam')
        self.message_user(request, f'⛔ {count} mesazh u shënua si spam.')
    mark_as_spam.short_description = '⛔ Marko si spam'


# ==================== NEWSLETTER SUBSCRIPTION ADMIN ====================

@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    """Admin për nënshkrime newsletter"""
    
    list_display = [
        'email', 'name_display', 'status_badge', 'subscribers_count', 'created_at'
    ]
    
    list_filter = [
        'is_active', 'created_at', 'unsubscribed_at'
    ]
    
    search_fields = [
        'email', 'name'
    ]
    
    readonly_fields = [
        'created_at', 'unsubscribed_at'
    ]
    
    fieldsets = (
        ('📧 Informacioni', {
            'fields': ('email', 'name')
        }),
        ('✅ Statusi', {
            'fields': ('is_active', 'created_at', 'unsubscribed_at')
        }),
    )
    
    actions = [
        'activate_subscriptions', 'deactivate_subscriptions', 'send_newsletter'
    ]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def name_display(self, obj):
        """Emri ose '-'"""
        return obj.name or '—'
    name_display.short_description = 'Emri'
    
    def status_badge(self, obj):
        """Status me badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 3px;">✅ Aktiv</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 8px; border-radius: 3px;">❌ Anulluar</span>'
            )
    status_badge.short_description = 'Statusi'
    status_badge.admin_order_field = 'is_active'
    
    def subscribers_count(self, obj):
        """Numri total i nënshkruesve"""
        count = NewsletterSubscription.objects.filter(is_active=True).count()
        return format_html('👥 {}', count)
    subscribers_count.short_description = 'Total'
    
    # ===== ACTIONS =====
    
    def activate_subscriptions(self, request, queryset):
        """Aktivizo nënshkrime"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'✅ {count} nënshkrim u aktivizua.')
    activate_subscriptions.short_description = '✅ Aktivizo'
    
    def deactivate_subscriptions(self, request, queryset):
        """Deaktivizo nënshkrime"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'❌ {count} nënshkrim u deaktivizua.')
    deactivate_subscriptions.short_description = '❌ Deaktivizo'
    
    def send_newsletter(self, request, queryset):
        """Shto në formën e dërgimit"""
        self.message_user(request, 'ℹ️ Shko në "Bulk Newsletter" për të dërguar email-a.')
    send_newsletter.short_description = '📬 Dërgoni newsletter'


# ==================== FAQ ADMIN ====================

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin për pyetje të shpeshta"""
    
    list_display = [
        'question_display', 'category_badge', 'views_display', 'is_active_badge', 'order'
    ]
    
    list_filter = [
        'category', 'is_active'
    ]
    
    search_fields = [
        'question', 'answer'
    ]
    
    readonly_fields = [
        'views', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('❓ Pyetja & Përgjigja', {
            'fields': ('question', 'answer', 'category')
        }),
        ('⚙️ Konfigurimi', {
            'fields': ('is_active', 'order', 'views')
        }),
        ('⏰ Kohë', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'activate_faqs', 'deactivate_faqs'
    ]
    
    ordering = ['category', 'order', 'id']
    
    def question_display(self, obj):
        """Pyetja e shkurtuar"""
        return obj.question[:60] + ('...' if len(obj.question) > 60 else '')
    question_display.short_description = 'Pyetja'
    
    def category_badge(self, obj):
        """Kategoria me badge"""
        colors = {
            'general': '#3498db',
            'booking': '#27ae60',
            'payment': '#f39c12',
            'guide': '#9b59b6',
            'cancellation': '#e74c3c',
            'technical': '#95a5a6',
        }
        color = colors.get(obj.category, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_category_display()
        )
    category_badge.short_description = 'Kategoria'
    category_badge.admin_order_field = 'category'
    
    def views_display(self, obj):
        """Shfaq shikimet"""
        return format_html('👁️ {}', obj.views)
    views_display.short_description = 'Shikimet'
    views_display.admin_order_field = 'views'
    
    def is_active_badge(self, obj):
        """Status aktiv"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 3px;">✅</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 8px; border-radius: 3px;">❌</span>'
            )
    is_active_badge.short_description = 'Aktiv'
    is_active_badge.admin_order_field = 'is_active'
    
    # ===== ACTIONS =====
    
    def activate_faqs(self, request, queryset):
        """Aktivizo pyetje"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'✅ {count} pyetje u aktivizua.')
    activate_faqs.short_description = '✅ Aktivizo'
    
    def deactivate_faqs(self, request, queryset):
        """Deaktivizo pyetje"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'❌ {count} pyetje u deaktivizua.')
    deactivate_faqs.short_description = '❌ Deaktivizo'


# ==================== SOCIAL LINK ADMIN ====================

@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    """Admin për lidhje shoqërore"""
    
    list_display = [
        'platform_with_icon', 'url_preview', 'is_active_badge', 'order'
    ]
    
    list_filter = [
        'is_active', 'platform'
    ]
    
    search_fields = [
        'platform', 'url'
    ]
    
    fieldsets = (
        ('🔗 Detajet', {
            'fields': ('platform', 'url', 'icon')
        }),
        ('⚙️ Konfigurimi', {
            'fields': ('is_active', 'order')
        }),
    )
    
    actions = [
        'activate_links', 'deactivate_links'
    ]
    
    ordering = ['order']
    
    def platform_with_icon(self, obj):
        """Platforma me ikonë"""
        icon_class_map = {
            'facebook': '👍',
            'instagram': '📸',
            'tiktok': '🎵',
            'youtube': '▶️',
            'twitter': '𝕏',
            'linkedin': '💼',
            'whatsapp': '💬',
        }
        icon = icon_class_map.get(obj.platform, '🔗')
        return format_html(
            '{} {}',
            icon, obj.get_platform_display()
        )
    platform_with_icon.short_description = 'Platforma'
    platform_with_icon.admin_order_field = 'platform'
    
    def url_preview(self, obj):
        """URL preview"""
        url_short = obj.url[:40] + ('...' if len(obj.url) > 40 else '')
        return format_html('<a href="{}" target="_blank">{}</a>', obj.url, url_short)
    url_preview.short_description = 'URL'
    
    def is_active_badge(self, obj):
        """Status aktiv"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 3px;">✅</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #e74c3c; color: white; padding: 3px 8px; border-radius: 3px;">❌</span>'
            )
    is_active_badge.short_description = 'Aktiv'
    is_active_badge.admin_order_field = 'is_active'
    
    # ===== ACTIONS =====
    
    def activate_links(self, request, queryset):
        """Aktivizo lidhje"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'✅ {count} lidhje u aktivizua.')
    activate_links.short_description = '✅ Aktivizo'
    
    def deactivate_links(self, request, queryset):
        """Deaktivizo lidhje"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'❌ {count} lidhje u deaktivizua.')
    deactivate_links.short_description = '❌ Deaktivizo'