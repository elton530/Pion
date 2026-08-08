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


def _owned_tour_or_404(tour_id, user):
    """Merr turin e një guide-i, ose ngre Tour.DoesNotExist."""
    return Tour.objects.get(id=tour_id, guide__user=user)


@login_required
@require_GET
def get_tour_status(request, tour_id):
    """Get current status of a tour (AJAX endpoint)"""
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
    try:
        data = json.loads(request.body)
        tour_id = data.get('tour_id')
        new_status = data.get('status')
        
        tour = _owned_tour_or_404(tour_id, request.user)
        old_status = tour.status
        
        # Validate status
        valid_statuses = [s[0] for s in TOUR_STATUS]
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': 'Invalid status'
            }, status=400)
        
        tour.status = new_status
        tour.save()
        
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
