import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Setup Google OAuth - ensures exactly one SocialApp exists for Google'

    def handle(self, *args, **options):
        client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')

        if not client_id or not client_secret:
            self.stdout.write(self.style.WARNING(
                'GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set. Skipping setup.'
            ))
            return

        google_apps = SocialApp.objects.filter(provider='google')
        count = google_apps.count()

        if count > 1:
            self.stdout.write(self.style.WARNING(
                f'Found {count} duplicate Google SocialApps. Cleaning up...'
            ))
            keep = google_apps.first()
            google_apps.exclude(id=keep.id).delete()
            keep.client_id = client_id
            keep.secret = client_secret
            keep.name = 'Google'
            keep.save()
            self.stdout.write(self.style.SUCCESS(
                f'Cleaned up duplicates. Kept SocialApp id={keep.id}'
            ))
        elif count == 1:
            app = google_apps.first()
            app.client_id = client_id
            app.secret = client_secret
            app.name = 'Google'
            app.save()
            self.stdout.write(self.style.SUCCESS(
                f'Updated existing Google SocialApp id={app.id}'
            ))
        else:
            app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=client_id,
                secret=client_secret,
            )
            self.stdout.write(self.style.SUCCESS(
                f'Created new Google SocialApp id={app.id}'
            ))

        site = Site.objects.get_current()
        app = SocialApp.objects.get(provider='google')
        if not app.sites.filter(id=site.id).exists():
            app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(
                f'Linked Google SocialApp to site: {site.domain}'
            ))

        self.stdout.write(self.style.SUCCESS('Google OAuth setup complete.'))