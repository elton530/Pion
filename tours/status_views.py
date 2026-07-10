"""
Tour Status Update Views
Real-time tour status tracking and updates
"""

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from tours.models import Tour
import json


@login_required
@require_GET
def get_tour_status(request, tour_id):
    """Get current status of a tour (AJAX endpoint)"""
    try:
        tour = Tour.objects.get(id=tour_id, guide=request.user)
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
        
        tour = Tour.objects.get(id=tour_id, guide=request.user)
        old_status = tour.status
        
        # Validate status
        valid_statuses = ['draft', 'published', 'hidden', 'cancelled', 'completed']
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
        tours = Tour.objects.filter(guide=request.user).values('id', 'status', 'confirmed_booked_spots', 'max_participants')
        return JsonResponse({
            'success': True,
            'tours': list(tours)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
