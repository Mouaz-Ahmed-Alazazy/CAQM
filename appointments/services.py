from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Appointment, DoctorAvailability, PatientForm
from accounts.models import Doctor, Patient
import logging

logger = logging.getLogger(__name__)


class AppointmentService:
    """
    Service layer for appointment management.
    """
    
    @staticmethod
    def get_available_slots(doctor_id, date):
        """
        Get available time slots for a doctor on a specific date.
        
        Args:
            doctor_id: ID of the doctor
            date: Date object or date string
            
        Returns:
            List of available time slots
        """
        try:
            doctor = Doctor.objects.get(pk=doctor_id)
            
            # Convert string to date if necessary
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d').date()
            
            return doctor.get_available_slots_for_date(date)
        except Doctor.DoesNotExist:
            logger.warning(f"Doctor with id {doctor_id} not found")
            return []
        except Exception as e:
            logger.error(f"Error getting available slots for doctor {doctor_id}: {e}")
            return []
    
    @staticmethod
    @transaction.atomic
    def book_appointment(patient, doctor, appointment_date, start_time, notes=''):
        """
        Book an appointment (with atomic transaction).
        Returns: Tuple (success: bool, appointment_or_error: Appointment/str)
        """
        try:
            # Calculate end time based on slot duration
            day_of_week = appointment_date.strftime('%A').upper()
            availability = DoctorAvailability.objects.filter(
                doctor=doctor,
                day_of_week=day_of_week,
                is_active=True
            ).first()
            
            if not availability:
                return False, 'Doctor is not available on this day'
            
            start_datetime = datetime.combine(appointment_date, start_time)
            end_datetime = start_datetime + timedelta(minutes=availability.slot_duration)
            end_time = end_datetime.time()
            
            # Create appointment
            appointment = Appointment(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                notes=notes,
                status='SCHEDULED'
            )
            
            appointment.save()
            
            return True, appointment
            
        except ValidationError as e:
            logger.warning(f"Validation error booking appointment: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error booking appointment: {e}", exc_info=True)
            return False, f'Booking failed: {str(e)}'
    
    @staticmethod
    def cancel_appointment(appointment_id, patient):
        """
        Cancel an appointment.
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                patient=patient,
                status='SCHEDULED'
            )
            appointment.status = 'CANCELLED'
            appointment.save()
            return True, 'Appointment cancelled successfully'
        except Appointment.DoesNotExist:
            logger.warning(f"Appointment {appointment_id} not found for cancellation")
            return False, 'Appointment not found or cannot be cancelled'
        except Exception as e:
            logger.error(f"Error cancelling appointment {appointment_id}: {e}")
            return False, str(e)
    
    @staticmethod
    @transaction.atomic
    def modify_appointment(appointment_id, patient, new_date=None, new_time=None, notes=None):
        """
        Modify an existing appointment.
        Returns:
            Tuple (success: bool, appointment_or_error: Appointment/str)
        """
        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                patient=patient,
                status='SCHEDULED'
            )
            
            # Update fields if provided
            if new_date:
                appointment.appointment_date = new_date
            if new_time:
                appointment.start_time = new_time
                # Recalculate end time
                day_of_week = appointment.appointment_date.strftime('%A').upper()
                availability = DoctorAvailability.objects.filter(
                    doctor=appointment.doctor,
                    day_of_week=day_of_week,
                    is_active=True
                ).first()
                
                if availability:
                    start_datetime = datetime.combine(appointment.appointment_date, new_time)
                    end_datetime = start_datetime + timedelta(minutes=availability.slot_duration)
                    appointment.end_time = end_datetime.time()
            
            if notes is not None:
                appointment.notes = notes
    
            appointment.save()
            logger.info(f"Appointment {appointment_id} modified successfully")
            return True, appointment
            
        except Appointment.DoesNotExist:
            logger.warning(f"Appointment {appointment_id} not found for modification")
            return False, 'Appointment not found or cannot be modified'
        except ValidationError as e:
            logger.warning(f"Validation error modifying appointment: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Error modifying appointment {appointment_id}: {e}", exc_info=True)
            return False, f'Modification failed: {str(e)}'
    
    @staticmethod
    def get_appointments_by_doctor(doctor, status=None, start_date=None, end_date=None):
        """
        Get appointments for a doctor with optional filtering.
        Returns:
            QuerySet of Appointment objects
        """
        try:
            queryset = Appointment.objects.filter(doctor=doctor)
            
            if status:
                queryset = queryset.filter(status=status)
            if start_date:
                queryset = queryset.filter(appointment_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(appointment_date__lte=end_date)
            
            return queryset.order_by('appointment_date', 'start_time')
        except Exception as e:
            logger.error(f"Error getting appointments for doctor {doctor.pk}: {e}")
            return Appointment.objects.none()
    
    @staticmethod
    def get_patient_appointments(patient, status=None):
        """
        Get appointments for a patient.
        Returns:
            QuerySet of Appointment objects
        """
        try:
            queryset = Appointment.objects.filter(patient=patient)
            
            if status:
                queryset = queryset.filter(status=status)
            
            return queryset.order_by('-appointment_date', '-start_time')
        except Exception as e:
            logger.error(f"Error getting appointments for patient {patient.pk}: {e}")
            return Appointment.objects.none()


class PatientFormService:
    """
    Service layer for patient medical form management.
    """
    
    @staticmethod
    @transaction.atomic
    def submit_form(patient, chief_complaint, medical_history='', current_medications='', allergies=''):
        """
        Submit a patient medical form.
        Returns:
            Tuple (success: bool, form_or_error: PatientForm/str)
        """
        try:
            form = PatientForm.objects.create(
                patient=patient,
                chief_complaint=chief_complaint,
                medical_history=medical_history,
                current_medications=current_medications,
                allergies=allergies
            )
            logger.info(f"Patient form {form.pk} submitted by patient {patient.pk}")
            return True, form
        except Exception as e:
            logger.error(f"Error submitting patient form: {e}", exc_info=True)
            return False, f'Failed to submit form: {str(e)}'
    
    @staticmethod
    def get_patient_forms(patient):
        """
        Get all forms submitted by a patient.
        Returns:
            QuerySet of PatientForm objects
        """
        try:
            return PatientForm.objects.filter(patient=patient).order_by('-submitted_at')
        except Exception as e:
            logger.error(f"Error getting forms for patient {patient.pk}: {e}")
            return PatientForm.objects.none()


class ScheduleService:
    """
    Service layer for doctor schedule management.
    """
    
    @staticmethod
    @transaction.atomic
    def update_schedule(doctor, schedule_data):
        """
        Update doctor's schedule (clear old slots and create new ones).
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Clear old slots for the days being updated
            days_to_update = [data['day_of_week'] for data in schedule_data]
            DoctorAvailability.objects.filter(
                doctor=doctor,
                day_of_week__in=days_to_update
            ).delete()
            
            # Create new availability slots
            created_slots = []
            for data in schedule_data:
                availability = DoctorAvailability.objects.create(
                    doctor=doctor,
                    day_of_week=data['day_of_week'],
                    start_time=data['start_time'],
                    end_time=data['end_time'],
                    slot_duration=data.get('slot_duration', 30),
                    is_active=data.get('is_active', True)
                )
                created_slots.append(availability)
            
            return True, f'Successfully created {len(created_slots)} availability slot(s)'
            
        except Exception as e:
            logger.error(f"Error updating schedule for doctor {doctor.pk}: {e}", exc_info=True)
            return False, f'Failed to update schedule: {str(e)}'
    
    @staticmethod
    def get_doctor_schedule(doctor):
        """
        Get doctor's current schedule.
        Returns:
            QuerySet of DoctorAvailability objects
        """
        try:
            return DoctorAvailability.objects.filter(doctor=doctor).order_by('day_of_week')
        except Exception as e:
            logger.error(f"Error getting schedule for doctor {doctor.pk}: {e}")
            return DoctorAvailability.objects.none()
