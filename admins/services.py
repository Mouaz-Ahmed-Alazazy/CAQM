from django.db import transaction
from django.db.models import Count, Q
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor
from nurses.models import Nurse
from queues.models import Queue, PatientQueue
from appointments.models import Appointment
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
            elif role == 'NURSE':
                Nurse.objects.create(
                    user=user,
                    assigned_doctor=kwargs.get('assigned_doctor')
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


class AdminDashboardService:
    """
    Service layer for admin dashboard statistics.
    Provides comprehensive queue and appointment analytics for all doctors.
    """
    
    @staticmethod
    def get_overview_stats():
        """Get high-level overview statistics."""
        today = timezone.now().date()
        return {
            'total_doctors': Doctor.objects.count(),
            'total_patients': Patient.objects.count(),
            'total_nurses': Nurse.objects.count(),
            'today_appointments': Appointment.objects.filter(appointment_date=today).count(),
            'active_queues': Queue.objects.filter(date=today).count(),
            'total_users': User.objects.count(),
        }
    
    @staticmethod
    def get_doctor_queue_stats(date_from=None, date_to=None):
        """
        Get comprehensive queue statistics for all doctors.
        Returns past, present, and future queue data.
        """
        today = timezone.now().date()
        
        if date_from is None:
            date_from = today - timedelta(days=30)
        if date_to is None:
            date_to = today + timedelta(days=30)
        
        doctors = Doctor.objects.select_related('user').all()
        doctor_stats = []
        
        for doctor in doctors:
            stats = {
                'doctor': doctor,
                'doctor_name': f"Dr. {doctor.user.get_full_name()}",
                'specialization': doctor.get_specialization_display(),
                'past': AdminDashboardService._get_past_stats(doctor, date_from, today),
                'today': AdminDashboardService._get_today_stats(doctor, today),
                'future': AdminDashboardService._get_future_stats(doctor, today, date_to),
            }
            doctor_stats.append(stats)
        
        return doctor_stats
    
    @staticmethod
    def _get_past_stats(doctor, date_from, today):
        """Get past queue statistics for a doctor."""
        past_queues = Queue.objects.filter(
            doctor=doctor,
            date__gte=date_from,
            date__lt=today
        )
        
        past_patient_queues = PatientQueue.objects.filter(
            queue__in=past_queues
        )
        
        total_booked = past_patient_queues.count()
        completed = past_patient_queues.filter(status='TERMINATED').count()
        no_shows = past_patient_queues.filter(status='NO_SHOW').count()
        
        completion_rate = round((completed / total_booked * 100), 1) if total_booked > 0 else 0
        
        return {
            'total_booked': total_booked,
            'completed': completed,
            'no_shows': no_shows,
            'completion_rate': completion_rate,
            'queue_days': past_queues.count(),
        }
    
    @staticmethod
    def _get_today_stats(doctor, today):
        """Get today's queue statistics for a doctor."""
        today_queue = Queue.objects.filter(doctor=doctor, date=today).first()
        
        if not today_queue:
            return {
                'has_queue': False,
                'waiting': 0,
                'in_progress': 0,
                'completed': 0,
                'no_shows': 0,
                'emergency': 0,
                'total': 0,
            }
        
        patient_queues = PatientQueue.objects.filter(queue=today_queue)
        
        return {
            'has_queue': True,
            'queue_id': today_queue.pk,
            'waiting': patient_queues.filter(status='WAITING').count(),
            'in_progress': patient_queues.filter(status='IN_PROGRESS').count(),
            'completed': patient_queues.filter(status='TERMINATED').count(),
            'no_shows': patient_queues.filter(status='NO_SHOW').count(),
            'emergency': patient_queues.filter(status='EMERGENCY').count(),
            'total': patient_queues.count(),
        }
    
    @staticmethod
    def _get_future_stats(doctor, today, date_to):
        """Get future appointments/queue statistics for a doctor."""
        future_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__gt=today,
            appointment_date__lte=date_to,
            status__in=['SCHEDULED', 'CHECKED_IN']
        )
        
        return {
            'scheduled_appointments': future_appointments.count(),
            'next_7_days': future_appointments.filter(
                appointment_date__lte=today + timedelta(days=7)
            ).count(),
        }
    
    @staticmethod
    def get_today_summary():
        """Get aggregated summary for today."""
        today = timezone.now().date()
        
        today_queues = PatientQueue.objects.filter(queue__date=today)
        today_appointments = Appointment.objects.filter(appointment_date=today)
        
        return {
            'total_in_queues': today_queues.count(),
            'waiting': today_queues.filter(status='WAITING').count(),
            'in_progress': today_queues.filter(status='IN_PROGRESS').count(),
            'completed': today_queues.filter(status='TERMINATED').count(),
            'no_shows': today_queues.filter(status='NO_SHOW').count(),
            'emergency': today_queues.filter(status='EMERGENCY').count(),
            'scheduled_appointments': today_appointments.filter(status='SCHEDULED').count(),
            'completed_appointments': today_appointments.filter(status='COMPLETED').count(),
        }
    
    @staticmethod
    def get_recent_activity(limit=10):
        """Get recent queue activity across all doctors."""
        recent = PatientQueue.objects.select_related(
            'patient__user', 'queue__doctor__user'
        ).order_by('-id')[:limit]
        
        return recent
