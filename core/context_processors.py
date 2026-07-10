from django.db.models import Avg, Sum
from tours.models import Tour
from users.models import GuideProfile


def site_stats(request):
    """Provide site-wide statistics for templates (footer, header, etc.)."""
    # Total active published tours
    tours_count = Tour.objects.filter(is_active=True, status='published').count()

    # Total active verified guides
    guides_count = GuideProfile.objects.filter(is_active=True, is_verified=True).count()

    # Weighted average rating across tours (weight by reviews_count)
    # Compute in Python to keep logic simple and avoid complex ORM expressions
    weighted_avg = 0.0
    total_reviews = 0
    qs = Tour.objects.filter(reviews_count__gt=0).values('average_rating', 'reviews_count')
    for t in qs:
        try:
            avg = float(t.get('average_rating') or 0)
            cnt = int(t.get('reviews_count') or 0)
            weighted_avg += avg * cnt
            total_reviews += cnt
        except Exception:
            continue

    site_avg_rating = 0.0
    if total_reviews > 0:
        site_avg_rating = round(weighted_avg / total_reviews, 1)

    return {
        'tours_count': tours_count,
        'guides_count': guides_count,
        'site_avg_rating': site_avg_rating,
    }
