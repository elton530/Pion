from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from tours.models import TourImage, Tour
import os
import urllib.parse


class Command(BaseCommand):
    help = 'Try to fix media file names for tours and tour images (replace spaces, decode URLs)'

    def handle(self, *args, **options):
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root:
            self.stderr.write('MEDIA_ROOT is not configured.')
            return

        def exists_in_storage(name):
            try:
                return default_storage.exists(name)
            except Exception:
                # Fallback to filesystem check
                return os.path.exists(os.path.join(media_root, name))

        def storage_path(name):
            try:
                return default_storage.path(name)
            except Exception:
                return os.path.join(media_root, name)

        def try_variants(name):
            variants = set()
            variants.add(name)
            variants.add(urllib.parse.unquote(name))
            variants.add(name.replace(' ', '_'))
            variants.add(name.replace(' ', '%20'))
            # basename variations
            dirname = os.path.dirname(name)
            basename = os.path.basename(name)
            variants.add(os.path.join(dirname, basename.replace(' ', '_')))
            variants.add(os.path.join(dirname, urllib.parse.unquote(basename)))
            return [v for v in variants]

        fixed = 0
        checked = 0

        # Fix TourImage objects
        for img in TourImage.objects.all():
            checked += 1
            if not img.image:
                continue
            name = img.image.name
            if exists_in_storage(name):
                continue

            found = None
            for variant in try_variants(name):
                if exists_in_storage(variant):
                    found = variant
                    break

            if found:
                # move/rename file to normalized name (replace spaces with underscore)
                new_basename = os.path.basename(name).replace(' ', '_')
                new_name = os.path.join(os.path.dirname(name), new_basename)
                src_path = storage_path(found)
                dst_path = storage_path(new_name)
                try:
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    os.rename(src_path, dst_path)
                    img.image.name = new_name
                    img.save(update_fields=['image'])
                    fixed += 1
                    self.stdout.write(f'Fixed TourImage id={img.id}: {found} -> {new_name}')
                except Exception as e:
                    self.stderr.write(f'Failed to move {src_path} -> {dst_path}: {e}')
            else:
                self.stderr.write(f'Missing file for TourImage id={img.id}: {name}')

        # Also check main_image/thumbnail on tours
        for tour in Tour.objects.all():
            for field in ('main_image', 'thumbnail'):
                checked += 1
                val = getattr(tour, field)
                if not val:
                    continue
                name = val.name
                if exists_in_storage(name):
                    continue

                found = None
                for variant in try_variants(name):
                    if exists_in_storage(variant):
                        found = variant
                        break

                if found:
                    new_basename = os.path.basename(name).replace(' ', '_')
                    new_name = os.path.join(os.path.dirname(name), new_basename)
                    src_path = storage_path(found)
                    dst_path = storage_path(new_name)
                    try:
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        os.rename(src_path, dst_path)
                        setattr(tour, field, new_name)
                        tour.save(update_fields=[field])
                        fixed += 1
                        self.stdout.write(f'Fixed Tour.{field} id={tour.id}: {found} -> {new_name}')
                    except Exception as e:
                        self.stderr.write(f'Failed to move {src_path} -> {dst_path}: {e}')
                else:
                    self.stderr.write(f'Missing file for Tour id={tour.id} field={field}: {name}')

        self.stdout.write(f'Done. Checked {checked} files, fixed {fixed} files.')
