from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator, EmailValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import json

# ==================== CHOICES ====================

SOCIAL_PLATFORMS = [
    ('facebook', 'Facebook'),
    ('instagram', 'Instagram'),
    ('tiktok', 'TikTok'),
    ('youtube', 'YouTube'),
    ('twitter', 'Twitter'),
    ('linkedin', 'LinkedIn'),
    ('whatsapp', 'WhatsApp'),
]

CONTACT_STATUS = [
    ('new', 'I ri'),
    ('replied', 'Përgjigjur'),
    ('resolved', 'Zgjidhur'),
    ('spam', 'Spam'),
]

FAQ_CATEGORY = [
    ('general', 'Pyetje Të Përgjithshme'),
    ('booking', 'Për Prenomet'),
    ('payment', 'Për Pagesat'),
    ('guide', 'Për Guide-t'),
    ('cancellation', 'Për Anulime'),
    ('technical', 'Problemat Teknike'),
]


# ==================== SITE SETTINGS MODEL ====================

class SiteSettings(models.Model):
    """Konfigurimi global i platformës"""
    
    # ===== SITE INFORMATION =====
    site_name = models.CharField(
        max_length=100,
        default='Tour Platform Albania',
        help_text='Emri i platformës'
    )
    
    site_description = models.TextField(
        default='Platforma për kërkimin dhe ofrimin e tureve në Shqipëri',
        help_text='Përshkrim i shkurtër i platformës'
    )
    
    site_logo = models.ImageField(
        upload_to='site/',
        blank=True,
        null=True,
        help_text='Logoja e platformës'
    )
    
    site_favicon = models.ImageField(
        upload_to='site/',
        blank=True,
        null=True,
        help_text='Favicon (ikona në tab)'
    )
    
    # ===== CONTACT INFORMATION =====
    contact_email = models.EmailField(
        default='info@tourplatform.al',
        help_text='Email për kontakt'
    )
    
    contact_phone = models.CharField(
        max_length=20,
        default='+355 4 2234 5678',
        help_text='Numri i telefonit'
    )
    
    contact_address = models.TextField(
        default='Tiranë, Shqipëri',
        help_text='Adresa fizike'
    )
    
    # ===== SOCIAL MEDIA =====
    facebook_url = models.URLField(
        blank=True,
        help_text='Facebook page URL'
    )
    
    instagram_url = models.URLField(
        blank=True,
        help_text='Instagram profile URL'
    )
    
    youtube_url = models.URLField(
        blank=True,
        help_text='YouTube channel URL'
    )
    
    tiktok_url = models.URLField(
        blank=True,
        help_text='TikTok profile URL'
    )
    
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='WhatsApp number (me +355...)'
    )
    
    # ===== LEGAL =====
    terms_and_conditions = models.TextField(
        blank=True,
        help_text='Kushtet dhe kondicionet e përdorimit'
    )
    
    privacy_policy = models.TextField(
        blank=True,
        help_text='Politika e privatësisë'
    )
    
    # ===== SETTINGS =====
    site_is_active = models.BooleanField(
        default=True,
        help_text='A është platforma aktive?'
    )
    
    maintenance_mode = models.BooleanField(
        default=False,
        help_text='Modaliteti i mirëmbajtjes'
    )
    
    maintenance_message = models.TextField(
        blank=True,
        help_text='Mesazhi i mirëmbajtjes'
    )
    
    # ===== SEO =====
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Meta title për SEO'
    )
    
    meta_description = models.TextField(
        max_length=300,
        blank=True,
        help_text='Meta description për SEO'
    )
    
    meta_keywords = models.TextField(
        blank=True,
        help_text='Meta keywords (të ndara me presje)'
    )
    
    # ===== EMAIL SETTINGS =====
    email_from_address = models.EmailField(
        default='noreply@tourplatform.al',
        help_text='Email për dërgim automatik'
    )
    
    email_notifications_enabled = models.BooleanField(
        default=True,
        help_text='A janë të aktivizuara emailat?'
    )
    
    # ===== SYSTEM =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Përkonfigurimi i Platformës'
        verbose_name_plural = 'Përkonfigurimi i Platformës'
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Sigurow vetëm 1 instancë
        if not self.pk and SiteSettings.objects.exists():
            self.pk = SiteSettings.objects.first().pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Merr settings globale"""
        return cls.objects.first() or cls.objects.create()


# ==================== CONTACT MESSAGE MODEL ====================

class ContactMessage(models.Model):
    """Mesazhe nga forma e kontaktit"""
    
    name = models.CharField(
        max_length=100,
        help_text='Emri i personës'
    )
    
    email = models.EmailField(
        help_text='Email për përgjigje'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Numri i telefonit (opsionale)'
    )
    
    subject = models.CharField(
        max_length=200,
        help_text='Tema e mesazhit'
    )
    
    message = models.TextField(
        help_text='Teksti i mesazhit'
    )
    
    status = models.CharField(
        max_length=20,
        choices=CONTACT_STATUS,
        default='new',
        help_text='Statusi i mesazhit'
    )
    
    reply_message = models.TextField(
        blank=True,
        help_text='Përgjigja e admin-it'
    )
    
    replied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='contact_replies',
        help_text='Personi që përgjigjet'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    replied_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Kur u përgjigj'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email']),
        ]
        verbose_name = 'Mesazh Kontakti'
        verbose_name_plural = 'Mesazhet e Kontaktit'
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    def mark_as_replied(self, reply_message, user):
        """Marko si përgjigjur"""
        self.status = 'replied'
        self.reply_message = reply_message
        self.replied_by = user
        self.replied_at = timezone.now()
        self.save()
    
    def mark_as_resolved(self):
        """Marko si zgjidhur"""
        self.status = 'resolved'
        self.save()
    
    def mark_as_spam(self):
        """Marko si spam"""
        self.status = 'spam'
        self.save()


# ==================== NEWSLETTER SUBSCRIPTION MODEL ====================

class NewsletterSubscription(models.Model):
    """Nënshkrime të newsletter-it"""
    
    email = models.EmailField(unique=True)
    
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Emri (opsionale)'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='A është aktive nënshkrimi?'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Kur u anullua nënshkrimi'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_active']),
        ]
        verbose_name = 'Nënshkrim Newsletter-i'
        verbose_name_plural = 'Nënshkrime Newsletter-i'
    
    def __str__(self):
        return self.email
    
    def unsubscribe(self):
        """Anuloje nënshkrimin"""
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()


# ==================== FAQ MODEL ====================

class FAQ(models.Model):
    """Pyetje të Shpeshta Bërë"""
    
    question = models.CharField(
        max_length=300,
        help_text='Pyetja'
    )
    
    answer = models.TextField(
        help_text='Përgjigja e detajuar'
    )
    
    category = models.CharField(
        max_length=50,
        choices=FAQ_CATEGORY,
        default='general',
        help_text='Kategoria e pyetjes'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='A është aktive?'
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text='Renditja e shfaqjes'
    )
    
    views = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text='Numri i shikimeve'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order', 'id']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]
        verbose_name = 'Pyetje të Shpeshtë'
        verbose_name_plural = 'Pyetje të Shpeshta'
    
    def __str__(self):
        return self.question[:100]
    
    def increment_views(self):
        """Shto në numrin e shikimeve"""
        self.views += 1
        self.save(update_fields=['views'])


# ==================== SOCIAL LINK MODEL ====================

class SocialLink(models.Model):
    """Lidhje të mediave shoqërore"""
    
    platform = models.CharField(
        max_length=50,
        choices=SOCIAL_PLATFORMS,
        help_text='Platforma'
    )
    
    url = models.URLField(
        help_text='URL e profilit'
    )
    
    icon = models.CharField(
        max_length=50,
        default='',
        blank=True,
        help_text='Emri i ikonës (FontAwesome)'
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text='Renditja e shfaqjes'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='A është aktive?'
    )
    
    class Meta:
        ordering = ['order']
        unique_together = ['platform']
        verbose_name = 'Lidhje Shoqërore'
        verbose_name_plural = 'Lidhje Shoqërore'
    
    def __str__(self):
        return f"{self.get_platform_display()}"
    
    @property
    def icon_class(self):
        """Merr klasën e ikonës"""
        icons = {
            'facebook': 'fab fa-facebook-f',
            'instagram': 'fab fa-instagram',
            'tiktok': 'fab fa-tiktok',
            'youtube': 'fab fa-youtube',
            'twitter': 'fab fa-twitter',
            'linkedin': 'fab fa-linkedin-in',
            'whatsapp': 'fab fa-whatsapp',
        }
        return icons.get(self.platform, 'fab fa-link')