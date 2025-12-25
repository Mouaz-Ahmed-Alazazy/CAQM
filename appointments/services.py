from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Appointment, DoctorAvailability
from .appointment_creators import ScheduledAppointmentCreator, WalkInAppointmentCreator

from .config import SingletonConfig
from doctors.models import Doctor
from patients.models import Patient
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
    def book_appointment(patient, doctor, appointment_date, start_time, notes='', is_walk_in=False):
        """
        Book an appointment using Factory Method pattern.
        
        Args:
            patient: Patient model instance
            doctor: Doctor model instance
            appointment_date: Date of the appointment
            start_time: Start time of the appointment
            notes: Optional notes for the appointment
            is_walk_in: If True, creates a walk-in appointment (immediately checked in)
            
        Returns:
            Tuple of (success: bool, appointment or error message)
        """
        try:
            # Select appropriate creator based on appointment type (Factory Method)
            if is_walk_in:
                creator = WalkInAppointmentCreator()
            else:
                creator = ScheduledAppointmentCreator()
            
            # Use factory method to create appointment
            try:
                appointment = creator.create_product(
                    patient=patient,
                    doctor=doctor,
                    appointment_date=appointment_date,
                    start_time=start_time,
                    notes=notes
                )
                appointment.save()
            except ValueError as e:
                return False, str(e)
            
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
        """
        try:
            queryset = Appointment.objects.filter(patient=patient)
            
            if status:
                queryset = queryset.filter(status=status)
            
            return queryset.order_by('-appointment_date', '-start_time')
        except Exception as e:
            logger.error(f"Error getting patient appointments: {e}")
            return Appointment.objects.none()





class ScheduleService:
    """
    Service layer for doctor schedule management.
    """
    
    @staticmethod
    @transaction.atomic
    def update_schedule(doctor, schedule_data):
        """
        Update doctor's schedule (clear old slots and create new ones).
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
        """
        try:
            return DoctorAvailability.objects.filter(doctor=doctor).order_by('day_of_week')
        except Exception as e:
            logger.error(f"Error getting schedule for doctor {doctor.pk}: {e}")
            return DoctorAvailability.objects.none()
