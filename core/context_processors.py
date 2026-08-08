from django.core.cache import cache
from django.db.models import Sum, F
from tours.models import Tour
from users.models import GuideProfile

STATS_CACHE_KEY = 'core:site_stats'
STATS_CACHE_TIMEOUT = 300  # 5 minuta


def site_stats(request):
    """Provide site-wide statistics for templates (footer, header, etc.)."""
    stats = cache.get(STATS_CACHE_KEY)

    if stats is None:
        # Total active published tours
        tours_count = Tour.objects.filter(is_active=True, status='published').count()

        # Total active verified guides
        guides_count = GuideProfile.objects.filter(is_active=True, is_verified=True).count()

        # Weighted average rating across tours (weight by reviews_count)
        agg = Tour.objects.filter(reviews_count__gt=0).aggregate(
            weighted=Sum(F('average_rating') * F('reviews_count')),
            reviews=Sum('reviews_count'),
        )
        weighted = agg['weighted'] or 0
        reviews = agg['reviews'] or 0
        site_avg_rating = round(weighted / reviews, 1) if reviews > 0 else 0.0

        stats = {
            'tours_count': tours_count,
            'guides_count': guides_count,
            'site_avg_rating': site_avg_rating,
        }
        cache.set(STATS_CACHE_KEY, stats, STATS_CACHE_TIMEOUT)

    return stats
