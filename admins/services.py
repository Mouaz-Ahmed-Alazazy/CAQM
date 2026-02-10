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
            validate_password(password)
            
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role,
                date_of_birth=kwargs.get('date_of_birth'),
                gender=kwargs.get('gender', 'MALE'),
            )
            
            if role == 'PATIENT':
                Patient.objects.create(
                    user=user,
                    address=kwargs.get('address', ''),
                    emergency_contact=kwargs.get('emergency_contact', '')
                )
            elif role == 'DOCTOR':
                Doctor.objects.create(
                    user=user,
                    specialization=kwargs.get('specialization'),
                    license_number=kwargs.get('license_number', ''),
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
            queryset = User.objects.all().order_by('-created_at')
            
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
            'total_doctors': User.objects.filter(role='DOCTOR').count(),
            'total_patients': User.objects.filter(role='PATIENT').count(),
            'total_nurses': User.objects.filter(role='NURSE').count(),
            'total_admins': User.objects.filter(role='ADMIN').count(),
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
    def get_recent_activity(limit=None):
        """Get recent queue activity across all doctors."""
        queryset = PatientQueue.objects.select_related(
            'patient__user', 'queue__doctor__user'
        ).order_by('-id')
        
        return queryset


class AdminAppointmentService:
    """Service layer for admin appointment management."""

    @staticmethod
    def get_appointments(doctor_id=None, date_from=None, date_to=None, status=None):
        queryset = Appointment.objects.select_related(
            'doctor__user', 'patient__user'
        ).order_by('-appointment_date', '-start_time')

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if date_from:
            queryset = queryset.filter(appointment_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(appointment_date__lte=date_to)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    @staticmethod
    @transaction.atomic
    def cancel_single_appointment(appointment_id, reason=''):
        from accounts.models import Notification
        try:
            appointment = Appointment.objects.select_related(
                'doctor__user', 'patient__user'
            ).get(pk=appointment_id)

            if appointment.status == 'CANCELLED':
                return False, 'Appointment is already cancelled'

            if appointment.status in ('COMPLETED', 'NO_SHOW'):
                return False, 'Cannot cancel a completed or no-show appointment'

            Appointment.objects.filter(pk=appointment_id).update(
                status='CANCELLED', updated_at=timezone.now()
            )

            recommendations = AdminAppointmentService._get_recommendations(
                appointment.doctor,
                appointment.patient,
                appointment.appointment_date
            )

            doctor_name = f"Dr. {appointment.doctor.user.get_full_name()}"
            cancel_reason = f" Reason: {reason}" if reason else ""

            Notification.objects.create(
                user=appointment.patient.user,
                notification_type='APPOINTMENT_CANCELLED',
                title='Appointment Cancelled',
                message=(
                    f'Your appointment with {doctor_name} on '
                    f'{appointment.appointment_date.strftime("%B %d, %Y")} at '
                    f'{appointment.start_time.strftime("%I:%M %p")} has been cancelled '
                    f'by the administrator.{cancel_reason}'
                ),
                recommendations=recommendations,
            )

            try:
                NotificationService.send_notification(
                    appointment.patient.user,
                    'BOOKING_CONFIRMATION',
                    context={
                        'doctor_name': doctor_name,
                        'date': appointment.appointment_date.strftime('%Y-%m-%d'),
                        'time': f'CANCELLED - {appointment.start_time.strftime("%I:%M %p")}',
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to send cancellation email: {e}")

            return True, 'Appointment cancelled and patient notified'

        except Appointment.DoesNotExist:
            return False, 'Appointment not found'
        except Exception as e:
            logger.error(f"Error cancelling appointment {appointment_id}: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    @transaction.atomic
    def cancel_doctor_appointments(doctor_id, date=None, reason=''):
        from accounts.models import Notification
        try:
            doctor = Doctor.objects.select_related('user').get(pk=doctor_id)
        except Doctor.DoesNotExist:
            return False, 'Doctor not found', 0

        queryset = Appointment.objects.filter(
            doctor=doctor,
            status__in=['SCHEDULED', 'CHECKED_IN']
        )
        if date:
            queryset = queryset.filter(appointment_date=date)

        appointments = queryset.select_related('patient__user')
        cancelled_count = 0
        doctor_name = f"Dr. {doctor.user.get_full_name()}"
        cancel_reason = f" Reason: {reason}" if reason else ""

        now = timezone.now()
        for appointment in appointments:
            Appointment.objects.filter(pk=appointment.pk).update(
                status='CANCELLED', updated_at=now
            )
            cancelled_count += 1

            recommendations = AdminAppointmentService._get_recommendations(
                doctor,
                appointment.patient,
                appointment.appointment_date
            )

            date_str = appointment.appointment_date.strftime("%B %d, %Y")
            time_str = appointment.start_time.strftime("%I:%M %p")

            if date:
                msg = (
                    f'Your appointment with {doctor_name} on {date_str} at {time_str} '
                    f'has been cancelled by the administrator.{cancel_reason}'
                )
            else:
                msg = (
                    f'All your appointments with {doctor_name} have been cancelled '
                    f'by the administrator. Your appointment on {date_str} at {time_str} '
                    f'is affected.{cancel_reason}'
                )

            Notification.objects.create(
                user=appointment.patient.user,
                notification_type='BULK_CANCELLATION',
                title=f'Appointment with {doctor_name} Cancelled',
                message=msg,
                recommendations=recommendations,
            )

        if cancelled_count == 0:
            return False, 'No active appointments found to cancel', 0

        return True, f'{cancelled_count} appointment(s) cancelled and patients notified', cancelled_count

    @staticmethod
    def _get_recommendations(doctor, patient, original_date):
        from doctors.models import DoctorAvailability
        recommendations = []

        same_doctor_appts = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__gt=original_date,
            appointment_date__lte=original_date + timedelta(days=30),
            status='SCHEDULED'
        ).values_list('appointment_date', 'start_time')
        booked_slots = {(a[0], a[1]) for a in same_doctor_appts}

        availabilities = DoctorAvailability.objects.filter(
            doctor=doctor, is_active=True
        )
        if availabilities.exists():
            from datetime import datetime
            check_date = original_date + timedelta(days=1)
            slots_found = 0
            while check_date <= original_date + timedelta(days=14) and slots_found < 3:
                day_name = check_date.strftime('%A').upper()
                avail = availabilities.filter(day_of_week=day_name).first()
                if avail:
                    start = datetime.combine(check_date, avail.start_time)
                    end = datetime.combine(check_date, avail.end_time)
                    slot_dur = timedelta(minutes=avail.slot_duration)
                    current = start
                    while current + slot_dur <= end and slots_found < 3:
                        if (check_date, current.time()) not in booked_slots:
                            recommendations.append({
                                'type': 'same_doctor',
                                'doctor_name': f"Dr. {doctor.user.get_full_name()}",
                                'specialization': doctor.get_specialization_display(),
                                'date': check_date.strftime('%Y-%m-%d'),
                                'date_display': check_date.strftime('%B %d, %Y'),
                                'time': current.time().strftime('%I:%M %p'),
                                'doctor_id': doctor.pk,
                            })
                            slots_found += 1
                            break
                        current += slot_dur
                check_date += timedelta(days=1)

        same_spec_doctors = Doctor.objects.filter(
            specialization=doctor.specialization
        ).exclude(pk=doctor.pk).select_related('user')

        for alt_doctor in same_spec_doctors[:3]:
            alt_avails = DoctorAvailability.objects.filter(
                doctor=alt_doctor, is_active=True
            )
            if alt_avails.exists():
                from datetime import datetime
                check_date = original_date
                found = False
                while check_date <= original_date + timedelta(days=14) and not found:
                    day_name = check_date.strftime('%A').upper()
                    avail = alt_avails.filter(day_of_week=day_name).first()
                    if avail:
                        alt_booked = Appointment.objects.filter(
                            doctor=alt_doctor,
                            appointment_date=check_date,
                            status__in=['SCHEDULED', 'CHECKED_IN']
                        ).count()
                        if alt_booked < 15:
                            start = datetime.combine(check_date, avail.start_time)
                            end = datetime.combine(check_date, avail.end_time)
                            slot_dur = timedelta(minutes=avail.slot_duration)
                            current = start
                            while current + slot_dur <= end:
                                is_booked = Appointment.objects.filter(
                                    doctor=alt_doctor,
                                    appointment_date=check_date,
                                    start_time=current.time(),
                                    status__in=['SCHEDULED', 'CHECKED_IN']
                                ).exists()
                                if not is_booked:
                                    recommendations.append({
                                        'type': 'same_specialization',
                                        'doctor_name': f"Dr. {alt_doctor.user.get_full_name()}",
                                        'specialization': alt_doctor.get_specialization_display(),
                                        'date': check_date.strftime('%Y-%m-%d'),
                                        'date_display': check_date.strftime('%B %d, %Y'),
                                        'time': current.time().strftime('%I:%M %p'),
                                        'doctor_id': alt_doctor.pk,
                                    })
                                    found = True
                                    break
                                current += slot_dur
                    check_date += timedelta(days=1)

        return recommendations
