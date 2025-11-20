from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Appointment, DoctorAvailability
from accounts.models import Doctor


class AppointmentService:
    """
    Service layer for appointment management.
    Encapsulates business logic as per the sequence diagram.
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
            return []
    
    @staticmethod
    @transaction.atomic
    def book_appointment(patient, doctor, appointment_date, start_time, notes=''):
        """
        Book an appointment (with atomic transaction).
        Matches sequence diagram: book_appointment -> create_appointment
        
        Args:
            patient: Patient object
            doctor: Doctor object
            appointment_date: Date object
            start_time: Time object
            notes: Optional notes
            
        Returns:
            Tuple (success: bool, appointment_or_error: Appointment/str)
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
            
            # Save will trigger full_clean() which validates business rules
            appointment.save()
            
            return True, appointment
            
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f'Booking failed: {str(e)}'
    
    @staticmethod
    def cancel_appointment(appointment_id, patient):
        """
        Cancel an appointment.
        
        Args:
            appointment_id: ID of the appointment
            patient: Patient object (to verify ownership)
            
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
            return False, 'Appointment not found or cannot be cancelled'
        except Exception as e:
            return False, str(e)


class ScheduleService:
    """
    Service layer for doctor schedule management.
    Matches sequence diagram for schedule updates.
    """
    
    @staticmethod
    @transaction.atomic
    def update_schedule(doctor, schedule_data):
        """
        Update doctor's schedule (clear old slots and create new ones).
        Matches sequence diagram: update_schedule -> clear_old_slots -> create_time_slots
        
        Args:
            doctor: Doctor object
            schedule_data: List of dicts with keys: day_of_week, start_time, end_time, slot_duration
            
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
            return False, f'Failed to update schedule: {str(e)}'
    
    @staticmethod
    def get_doctor_schedule(doctor):
        """
        Get doctor's current schedule.
        
        Args:
            doctor: Doctor object
            
        Returns:
            QuerySet of DoctorAvailability objects
        """
        return DoctorAvailability.objects.filter(doctor=doctor).order_by('day_of_week')
