from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor
from accounts.notifications import NotificationService
import logging

logger = logging.getLogger(__name__)


class AdminService:
    """
    Service layer for admin user management.
    Handles user registration by administrators.
    """
    
    @staticmethod
    @transaction.atomic
    def register_user(email, password, first_name, last_name, phone, role, **kwargs):
        """
        Register a new user (Patient, Doctor, or Admin).
        """
        try:
            # Validate password
            validate_password(password)
            
            # Create user
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role
            )
            
            # Create role-specific profile
            if role == 'PATIENT':
                Patient.objects.create(
                    user=user,
                    date_of_birth=kwargs.get('date_of_birth'),
                    address=kwargs.get('address', ''),
                    emergency_contact=kwargs.get('emergency_contact', '')
                )
            elif role == 'DOCTOR':
                Doctor.objects.create(
                    user=user,
                    specialization=kwargs.get('specialization'),
                    license_number=kwargs.get('license_number', ''),
                    years_of_experience=kwargs.get('years_of_experience', 0)
                )
            
            # Send registration confirmation
            try:
                NotificationService.send_registration_confirmation(user)
            except Exception as e:
                logger.warning(f"Failed to send registration email: {e}")
                # Don't fail registration if email fails
            
            logger.info(f"User {email} registered successfully with role {role}")
            return True, user
            
        except ValidationError as e:
            logger.warning(f"Validation error during user registration: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Error registering user: {e}", exc_info=True)
            return False, f'Registration failed: {str(e)}'
    
    @staticmethod
    def get_all_users(role=None):
        """
        Get all users, optionally filtered by role.
        """
        try:
            queryset = User.objects.all().order_by('-date_joined')
            
            if role:
                queryset = queryset.filter(role=role)
            
            return queryset
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return User.objects.none()
    
    @staticmethod
    def delete_user(user_id):
        """
        Delete a user.
        """
        try:
            user = User.objects.get(pk=user_id)
            email = user.email
            user.delete()
            logger.info(f"User {email} deleted successfully")
            return True, 'User deleted successfully'
        except User.DoesNotExist:
            logger.warning(f"User {user_id} not found for deletion")
            return False, 'User not found'
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False, str(e)
