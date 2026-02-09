from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from patients.models import Patient
import logging

logger = logging.getLogger(__name__)

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to handle social account sign up
    """

    def pre_social_login(self, request, sociallogin):
        """
        Called after successful social account login, before the login is actually processed
        """
        # Check if the user already has an account
        if sociallogin.is_existing:
            return
        # Check if email is already in use
        if sociallogin.user.id:
            return

        # try to connect to existing user with same email
        try:
            email = sociallogin.account.extra_data.get('email', '').lower()
            if email:
                from accounts.models import User
                existing_user = User.objects.filter(email=email).first()
                if existing_user:
                    # Connect the social account to existing user
                    sociallogin.connect(request, existing_user)
        except Exception as e:
            logger.error(f"Error in pre_social_login: {e}")

    def save_user(self, request, sociallogin, form=None):
        """
        Save the user as a patient
        """
        user = super().save_user(request, sociallogin, form)
        extra_data = sociallogin.account.extra_data

        user.role = "PATIENT"
        if not user.first_name and extra_data.get('given_name'):
            user.first_name = extra_data.get('given_name')
        if not user.last_name and extra_data.get('family_name'):
            user.last_name = extra_data.get('family_name')
        if not user.phone and extra_data.get('phone'):
            user.phone = extra_data.get('phone')
        if not user.date_of_birth and extra_data.get('birthdate'):
            user.date_of_birth = extra_data.get('birthdate')
        if not user.gender and extra_data.get('gender'):
            user.gender = extra_data.get('gender')
        user.save()
        
        # create patient profile if does not exist
        if not hasattr(user, 'patient_profile'):
            try:
                Patient.objects.create(user=user)
                logger.info(f"Created patient profile for user: {user}")
            except Exception as e:
                logger.error(f"Error creating patient profile: {e}")
        
        return user

    def populate_user(self, request, sociallogin, data):
        """
        Populate the user with data from the social account
        """
        user = super().populate_user(request, sociallogin, data)
        extra_data = sociallogin.account.extra_data
        
        user.phone = data.get('phone')
        user.date_of_birth = data.get('birthdate')
        user.gender = data.get('gender')
        user.save()
        return user


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter for regular account operations.
    """

    def save_user(self, request, user, form, commit=True):
        """
        Save the user as a patient
        """
        user = super().save_user(request, user, form, commit=False)
        user.role = "PATIENT"
        if commit:
            user.save()
            if not hasattr(user, 'patient_profile'):
                try:
                    Patient.objects.create(user=user)
                    logger.info(f"Created patient profile for user: {user}")
                except Exception as e:
                    logger.error(f"Error creating patient profile: {e}")
        return user
        