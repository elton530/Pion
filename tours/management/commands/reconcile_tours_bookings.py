from django.core.management.base import BaseCommand
from tours.models import Tour
from bookings.models import Booking
from django.db.models import Sum, Q

class Command(BaseCommand):
    help = 'Reconcile Tour.available_spots and Tour.booking_count against Booking records. Run with --apply to write fixes.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Apply fixes instead of dry-run')
        parser.add_argument('--tour', type=str, help='Optional tour slug to reconcile only one tour')

    def handle(self, *args, **options):
        apply = options['apply']
        tour_slug = options.get('tour')

        qs = Tour.objects.all()
        if tour_slug:
            qs = qs.filter(slug=tour_slug)

        total = qs.count()
        self.stdout.write(f'Found {total} tours to check...')

        for tour in qs.iterator():
            # Sum of num_people for bookings that are not cancelled
            reserved = Booking.objects.filter(tour=tour).exclude(status='cancelled').aggregate(total=Sum('num_people'))['total'] or 0
            # booking_count should reflect confirmed/completed
            confirmed_count = Booking.objects.filter(tour=tour, status__in=['confirmed','completed']).count()

            expected_available = max(0, tour.max_participants - reserved)
            expected_booking_count = confirmed_count

            issues = []
            if tour.available_spots != expected_available:
                issues.append(f'available_spots: db={tour.available_spots} expected={expected_available}')
            if tour.booking_count != expected_booking_count:
                issues.append(f'booking_count: db={tour.booking_count} expected={expected_booking_count}')

            if issues:
                self.stdout.write(f'[{tour.slug}] {tour.title}:')
                for i in issues:
                    self.stdout.write(f'  - {i}')

                if apply:
                    updates = []
                    if tour.available_spots != expected_available:
                        tour.available_spots = expected_available
                        updates.append('available_spots')
                    if tour.booking_count != expected_booking_count:
                        tour.booking_count = expected_booking_count
                        updates.append('booking_count')
                    tour.save(update_fields=updates + ['updated_at'] if updates else ['updated_at'])
                    self.stdout.write(self.style.SUCCESS(f'  -> Fixed fields: {updates}'))
                else:
                    self.stdout.write(self.style.WARNING('  -> Dry run (use --apply to fix)'))
            else:
                self.stdout.write(f'[{tour.slug}] OK')

        self.stdout.write(self.style.SUCCESS('Reconciliation complete.'))
