from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import redirect
from patients.models import Patient
import logging

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        try:
            email = sociallogin.account.extra_data.get('email', '').lower()
            if email:
                from accounts.models import User
                existing_user = User.objects.filter(email=email).first()
                if existing_user:
                    sociallogin.connect(request, existing_user)
        except Exception as e:
            logger.error(f"Error in pre_social_login: {e}")

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        extra_data = sociallogin.account.extra_data

        user.role = "PATIENT"
        if extra_data.get('given_name') and not user.first_name:
            user.first_name = extra_data['given_name']
        if extra_data.get('family_name') and not user.last_name:
            user.last_name = extra_data['family_name']
        user.save()

        if not Patient.objects.filter(user=user).exists():
            try:
                Patient.objects.create(user=user)
                logger.info(f"Created patient profile for Google user: {user.email}")
            except Exception as e:
                logger.error(f"Error creating patient profile: {e}")

        return user

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        return user

    def get_login_redirect_url(self, request):
        user = request.user
        if user.is_authenticated and (not user.date_of_birth or not user.phone):
            return '/accounts/profile/update'
        if user.is_authenticated and user.is_patient():
            return '/patients/'
        return '/patients/'


class CustomAccountAdapter(DefaultAccountAdapter):

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.role = "PATIENT"
        if commit:
            user.save()
            if not Patient.objects.filter(user=user).exists():
                try:
                    Patient.objects.create(user=user)
                    logger.info(f"Created patient profile for user: {user.email}")
                except Exception as e:
                    logger.error(f"Error creating patient profile: {e}")
        return user

    def get_login_redirect_url(self, request):
        user = request.user
        if user.is_authenticated:
            if user.is_doctor():
                return '/doctors/dashboard/'
            elif user.is_nurse():
                return '/nurses/dashboard/'
            elif user.is_admin():
                return '/admins/'
            elif not user.date_of_birth or not user.phone:
                return '/accounts/profile/update'
        return '/patients/'
