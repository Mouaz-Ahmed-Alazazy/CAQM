"""
Tests for AppointmentService success paths.
Exception handling is already covered in test_service_exceptions.py
"""
import pytest
from django.utils import timezone
from datetime import time, timedelta
from appointments.services import AppointmentService
from appointments.models import Appointment
from doctors.models import DoctorAvailability


@pytest.mark.django_db
class TestAppointmentServiceSuccessPaths:
    """Test AppointmentService success scenarios"""
    
    def test_book_appointment_scheduled_success(self, patient, doctor):
        """Test successful scheduled appointment booking"""
        future_date = timezone.now().date() + timedelta(days=7)  # Next week
        # Ensure it's Monday (doctor has availability)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        success, appointment = AppointmentService.book_appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(10, 0),
            notes='Regular checkup',
            is_walk_in=False
        )
        
        assert success is True
        assert isinstance(appointment, Appointment)
        assert appointment.patient == patient
        assert appointment.doctor == doctor
        assert appointment.status == 'SCHEDULED'
        assert appointment.start_time == time(10, 0)
        assert appointment.end_time == time(10, 30)
        assert appointment.notes == 'Regular checkup'
    
    def test_book_appointment_walk_in_success(self, patient, doctor):
        """Test successful walk-in appointment booking"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        success, appointment = AppointmentService.book_appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(11, 0),
            notes='Emergency',
            is_walk_in=True
        )
        
        assert success is True
        assert appointment.status == 'CHECKED_IN'  # Walk-ins are auto checked-in
        assert 'Walk-in appointment' in appointment.notes
        assert 'Emergency' in appointment.notes
    
    def test_book_appointment_uses_correct_creator(self, patient, doctor, db):
        """Test correct factory creator is selected based on is_walk_in flag"""
        from accounts.models import User
        from doctors.models import Doctor, DoctorAvailability
        
        # Create a second doctor with different specialization to avoid validation error
        doctor2_user = User.objects.create_user(
            email='doctor2@example.com',
            password='password123',
            first_name='Second',
            last_name='Doctor',
            date_of_birth='1980-01-01',
            role='DOCTOR',
            phone='0931234567'
        )
        doctor2 = Doctor.objects.create(
            user=doctor2_user,
            specialization='DERMATOLOGY',  # Different specialization
            license_number='LIC67890'
        )
        
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        # Create availability for doctor2
        DoctorAvailability.objects.create(
            doctor=doctor2,
            day_of_week='MONDAY',
            start_time=time(9, 0),
            end_time=time(17, 0),
            slot_duration=30
        )
        
        # Book scheduled with doctor1
        success1, appt1 = AppointmentService.book_appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(9, 0),
            is_walk_in=False
        )
        
        # Book walk-in with doctor2 (different specialization, same day is OK)
        success2, appt2 = AppointmentService.book_appointment(
            patient=patient,
            doctor=doctor2,
            appointment_date=next_monday,
            start_time=time(14, 0),
            is_walk_in=True
        )
        
        assert success1 is True
        assert success2 is True
        assert appt1.status == 'SCHEDULED'
        assert appt2.status == 'CHECKED_IN'
    
    def test_get_available_slots_returns_valid_slots(self, doctor):
        """Test slot retrieval for available doctor"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        slots = AppointmentService.get_available_slots(
            doctor_id=doctor.pk,
            date=next_monday
        )
        
        # Should have slots (9:00-17:00, 30 min intervals, max 15)
        assert len(slots) > 0
        assert time(9, 0) in slots
        assert time(16, 0) in slots
    
    def test_get_available_slots_filters_booked_times(self, doctor, patient):
        """Test booked times are excluded from available slots"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        # Book 10:00 slot
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        
        slots = AppointmentService.get_available_slots(
            doctor_id=doctor.pk,
            date=next_monday
        )
        
        # 10:00 should not be available
        assert time(10, 0) not in slots
        # But 9:00 should still be available
        assert time(9, 0) in slots
    
    def test_get_available_slots_accepts_string_date(self, doctor):
        """Test get_available_slots accepts date as string"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        date_string = next_monday.strftime('%Y-%m-%d')
        
        slots = AppointmentService.get_available_slots(
            doctor_id=doctor.pk,
            date=date_string
        )
        
        assert len(slots) > 0
    
    def test_modify_appointment_updates_date(self, patient, doctor):
        """Test modifying appointment date"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        
        new_date = next_monday + timedelta(days=7)  # Week later
        
        success, result = AppointmentService.modify_appointment(
            appointment_id=appointment.pk,
            patient=patient,
            new_date=new_date
        )
        
        assert success is True
        assert isinstance(result, Appointment)
        assert result.appointment_date == new_date
    
    def test_modify_appointment_updates_time(self, patient, doctor):
        """Test modifying appointment time"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        
        success, result = AppointmentService.modify_appointment(
            appointment_id=appointment.pk,
            patient=patient,
            new_time=time(14, 0)
        )
        
        assert success is True
        assert result.start_time == time(14, 0)
    
    def test_modify_appointment_updates_notes(self, patient, doctor):
        """Test modifying appointment notes"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED',
            notes='Original note'
        )
        
        success, result = AppointmentService.modify_appointment(
            appointment_id=appointment.pk,
            patient=patient,
            notes='Updated note'
        )
        
        assert success is True
        assert result.notes == 'Updated note'
    
    def test_modify_appointment_recalculates_end_time(self, patient, doctor):
        """Test end time is recalculated when time changes"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        
        success, result = AppointmentService.modify_appointment(
            appointment_id=appointment.pk,
            patient=patient,
            new_time=time(15, 0)
        )
        
        assert success is True
        # End time should be recalculated (15:00 + 30 min = 15:30)
        assert result.end_time == time(15, 30)
    
    def test_get_appointments_by_doctor_no_filters(self, doctor, patient):
        """Test retrieving all doctor appointments without filters"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        # Create multiple appointments on different days to avoid validation error
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status='SCHEDULED'
        )
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday + timedelta(days=7),  # Different day
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='CHECKED_IN'
        )
        
        appointments = AppointmentService.get_appointments_by_doctor(doctor)
        
        assert appointments.count() >= 2
    
    def test_get_appointments_by_doctor_with_status_filter(self, doctor, patient):
        """Test filtering doctor appointments by status"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        # Create appointments on different days to avoid validation error
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status='SCHEDULED'
        )
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday + timedelta(days=7),  # Different day
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='COMPLETED'
        )
        
        scheduled = AppointmentService.get_appointments_by_doctor(
            doctor, 
            status='SCHEDULED'
        )
        
        assert scheduled.count() >= 1
        for appt in scheduled:
            assert appt.status == 'SCHEDULED'
    
    def test_get_appointments_by_doctor_with_date_range(self, doctor, patient):
        """Test filtering doctor appointments by date range"""
        today = timezone.now().date()
        future1 = today + timedelta(days=7)
        future2 = today + timedelta(days=14)
        future3 = today + timedelta(days=21)
        
        # Adjust to Mondays
        for date in [future1, future2, future3]:
            days_ahead = 0 - date.weekday()
            if days_ahead < 0:
                days_ahead += 7
            date = date + timedelta(days=days_ahead)
        
        days_ahead = 0 - future1.weekday()
        if days_ahead < 0:
            days_ahead += 7
        monday1 = future1 + timedelta(days=days_ahead)
        
        days_ahead = 0 - future2.weekday()
        if days_ahead < 0:
            days_ahead += 7
        monday2 = future2 + timedelta(days=days_ahead)
        
        days_ahead = 0 - future3.weekday()
        if days_ahead < 0:
            days_ahead += 7
        monday3 = future3 + timedelta(days=days_ahead)
        
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=monday1,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status='SCHEDULED'
        )
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=monday2,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=monday3,
            start_time=time(11, 0),
            end_time=time(11, 30),
            status='SCHEDULED'
        )
        
        # Get appointments in middle range
        appointments = AppointmentService.get_appointments_by_doctor(
            doctor,
            start_date=monday1,
            end_date=monday2
        )
        
        # Should include first two, not the third
        dates = [appt.appointment_date for appt in appointments]
        assert monday1 in dates
        assert monday2 in dates
        assert monday3 not in dates
    
    def test_get_patient_appointments_no_filter(self, patient, doctor):
        """Test retrieving all patient appointments"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        # Create appointments on different days to avoid validation error
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status='SCHEDULED'
        )
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday + timedelta(days=7),  # Different day
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='COMPLETED'
        )
        
        appointments = AppointmentService.get_patient_appointments(patient)
        
        assert appointments.count() >= 2
    
    def test_get_patient_appointments_with_status_filter(self, patient, doctor):
        """Test filtering patient appointments by status"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        # Create appointments on different days to avoid validation error
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status='SCHEDULED'
        )
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday + timedelta(days=7),  # Different day
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='CANCELLED'
        )
        
        scheduled = AppointmentService.get_patient_appointments(
            patient,
            status='SCHEDULED'
        )
        
        assert scheduled.count() >= 1
        for appt in scheduled:
            assert appt.status == 'SCHEDULED'
    
    def test_cancel_appointment_success(self, patient, doctor):
        """Test successfully cancelling an appointment"""
        future_date = timezone.now().date() + timedelta(days=7)
        days_ahead = 0 - future_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_monday = future_date + timedelta(days=days_ahead)
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        
        success, message = AppointmentService.cancel_appointment(
            appointment_id=appointment.pk,
            patient=patient
        )
        
        assert success is True
        assert 'success' in message.lower()
        
        appointment.refresh_from_db()
        assert appointment.status == 'CANCELLED'
