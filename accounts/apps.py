import os
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(self._setup_google_oauth, sender=self)

    @staticmethod
    def _setup_google_oauth(sender, **kwargs):
        try:
            from django.contrib.sites.models import Site
            from allauth.socialaccount.models import SocialApp

            client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')

            if not client_id or not client_secret:
                return

            google_apps = SocialApp.objects.filter(provider='google')
            count = google_apps.count()

            if count > 1:
                keep = google_apps.first()
                google_apps.exclude(id=keep.id).delete()
                keep.client_id = client_id
                keep.secret = client_secret
                keep.name = 'Google'
                keep.save()
                app = keep
            elif count == 1:
                app = google_apps.first()
                if app.client_id != client_id or app.secret != client_secret:
                    app.client_id = client_id
                    app.secret = client_secret
                    app.save()
            else:
                app = SocialApp.objects.create(
                    provider='google',
                    name='Google',
                    client_id=client_id,
                    secret=client_secret,
                )

            site = Site.objects.get_current()
            if not app.sites.filter(id=site.id).exists():
                app.sites.add(site)

        except Exception as e:
            logger.debug(f"Google OAuth auto-setup skipped: {e}")
