"""
Tour Status Update Views
Real-time tour status tracking and updates
"""

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from tours.models import Tour, TOUR_STATUS
import json


ALLOWED_TOUR_STATUS_TRANSITIONS = {
    "draft": {"published", "hidden", "cancelled"},
    "published": {"draft", "hidden", "cancelled", "completed"},
    "hidden": {"draft", "published", "cancelled"},
    "cancelled": set(),
    "completed": set(),
}


def _owned_tour_or_404(tour_id, user):
    """Merr turin e një guide-i, ose ngre Tour.DoesNotExist."""
    return Tour.objects.get(id=tour_id, guide__user=user)


def _is_guide_user(user):
    return hasattr(user, 'guide_profile')


@login_required
@require_GET
def get_tour_status(request, tour_id):
    """Get current status of a tour (AJAX endpoint)"""
    if not _is_guide_user(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Only guides can access this endpoint'
        }, status=403)

    try:
        tour = _owned_tour_or_404(tour_id, request.user)
        return JsonResponse({
            'success': True,
            'status': tour.status,
            'status_display': tour.get_status_display(),
            'confirmed_spots': tour.confirmed_booked_spots,
            'max_participants': tour.max_participants,
            'updated_at': tour.updated_at.isoformat() if hasattr(tour, 'updated_at') else None
        })
    except Tour.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Tour not found'
        }, status=404)


@login_required
@require_POST
def update_tour_status(request):
    """Update tour status (AJAX endpoint)"""
    if not _is_guide_user(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Only guides can access this endpoint'
        }, status=403)

    try:
        data = json.loads(request.body)
        tour_id = data.get('tour_id')
        new_status = data.get('status')

        if not tour_id:
            return JsonResponse({
                'success': False,
                'error': 'tour_id is required'
            }, status=400)

        if not new_status:
            return JsonResponse({
                'success': False,
                'error': 'status is required'
            }, status=400)
        
        tour = _owned_tour_or_404(tour_id, request.user)
        old_status = tour.status
        
        # Validate status
        valid_statuses = [s[0] for s in TOUR_STATUS]
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': 'Invalid status'
            }, status=400)

        allowed_targets = ALLOWED_TOUR_STATUS_TRANSITIONS.get(old_status, set())
        if new_status != old_status and new_status not in allowed_targets:
            return JsonResponse({
                'success': False,
                'error': f'Invalid status transition: {old_status} -> {new_status}'
            }, status=400)
        
        tour.status = new_status
        tour.save(update_fields=['status', 'updated_at'])
        
        return JsonResponse({
            'success': True,
            'message': f'Statusi ndryshuar nga {old_status} në {new_status}',
            'old_status': old_status,
            'new_status': new_status,
            'status_display': tour.get_status_display()
        })
    except Tour.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Tour not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_GET
def get_guide_tours_status(request):
    """Get all tours status for guide (AJAX endpoint for bulk updates)"""
    if not _is_guide_user(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Only guides can access this endpoint'
        }, status=403)

    try:
        tours = (
            Tour.objects.filter(guide__user=request.user)
            .annotate(
                confirmed_spots=Coalesce(
                    Sum(
                        'bookings__num_people',
                        filter=Q(bookings__status__in=['confirmed', 'completed']),
                    ),
                    0,
                )
            )
            .values('id', 'status', 'confirmed_spots', 'max_participants')
        )
        return JsonResponse({
            'success': True,
            'tours': list(tours)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
