from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from .models import Appointment, DoctorAvailability


class AppointmentCreator(ABC):
    """
    Abstract creator class defining the factory method.
    """
    
    @abstractmethod
    def create_product(self, patient, doctor, appointment_date, start_time, notes='') -> Appointment:
        """
        Factory method that concrete creators must implement.
        """
        pass
    
    def _calculate_end_time(self, doctor, appointment_date, start_time):
        """
        Looks up the doctor's availability for the given day and calculates
        the end time based on the slot duration.
        """
        day_of_week = appointment_date.strftime('%A').upper()
        availability = DoctorAvailability.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            is_active=True
        ).first()
        
        if not availability:
            raise ValueError('Doctor is not available on this day')
        
        start_datetime = datetime.combine(appointment_date, start_time)
        end_datetime = start_datetime + timedelta(minutes=availability.slot_duration)
        return end_datetime.time()


class ScheduledAppointmentCreator(AppointmentCreator):
    """
    Concrete creator for normal scheduled appointments.
    """
    
    def create_product(self, patient, doctor, appointment_date, start_time, notes='') -> Appointment:
        """
        Create a scheduled appointment.
        """
        end_time = self._calculate_end_time(doctor, appointment_date, start_time)
        
        return Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            notes=notes,
            status='SCHEDULED'
        )


class WalkInAppointmentCreator(AppointmentCreator):
    """
    Concrete creator for walk-in/emergency appointments.
    """
    
    def create_product(self, patient, doctor, appointment_date, start_time, notes='') -> Appointment:
        """
        Create a walk-in appointment.
        """
        end_time = self._calculate_end_time(doctor, appointment_date, start_time)
        
        # Walk-ins are immediately checked in
        walk_in_notes = f"Walk-in appointment. {notes}" if notes else "Walk-in appointment."
        
        return Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            notes=walk_in_notes,
            status='CHECKED_IN'
        )


class AdminAppointmentCreator(AppointmentCreator):
    """
    Concrete creator for appointments created by administrators.
    """
    
    def create_product(self, patient, doctor, appointment_date, start_time, notes='') -> Appointment:
        """
        Create an admin-managed appointment.
        """
        end_time = self._calculate_end_time(doctor, appointment_date, start_time)
        
        admin_notes = f"[ADMIN] {notes}" if notes else "[ADMIN] Created by administrator."
        
        return Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            notes=admin_notes,
            status='SCHEDULED'
        )

