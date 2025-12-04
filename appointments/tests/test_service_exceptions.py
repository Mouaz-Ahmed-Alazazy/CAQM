"""
Tests for service layer exception handling and error paths.
Tests DoesNotExist, ValidationError, and general exception scenarios.
"""
import pytest
from unittest.mock import patch, Mock
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import DatabaseError
from datetime import time, timedelta
from appointments.services import AppointmentService, PatientFormService, ScheduleService
from appointments.models import Appointment, DoctorAvailability


@pytest.mark.django_db
class TestAppointmentServiceExceptions:
    """Test AppointmentService exception handling"""
    
    def test_get_available_slots_invalid_doctor_id(self):
        """Test get_available_slots with non-existent doctor returns empty list"""
        slots = AppointmentService.get_available_slots(
            doctor_id=9999,  # Non-existent
            date=timezone.now().date()
        )
        
        assert slots == []
    
    def test_get_available_slots_invalid_date_format(self):
        """Test get_available_slots with invalid date format returns empty list"""
        slots = AppointmentService.get_available_slots(
            doctor_id=1,
            date='invalid-date'  # Invalid format
        )
        
        assert slots == []
    
    @patch('appointments.services.Doctor.objects.get')
    def test_get_available_slots_database_error(self, mock_get):
        """Test get_available_slots handles database errors gracefully"""
        mock_get.side_effect = DatabaseError("Database connection failed")
        
        slots = AppointmentService.get_available_slots(
            doctor_id=1,
            date=timezone.now().date()
        )
        
        assert slots == []
    
    def test_book_appointment_no_availability(self, patient, doctor):
        """Test booking when doctor has no availability returns error"""
        # Don't create any availability for the doctor
        future_date = timezone.now().date() + timedelta(days=1)
        
        success, result = AppointmentService.book_appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=future_date,
            start_time=time(10, 0),
            notes='Test'
        )
        
        assert success is False
        assert 'not available' in result
    
    def test_book_appointment_validation_error_past_date(self, patient, doctor):
        """Test booking with past date triggers ValidationError"""
        past_date = timezone.now().date() - timedelta(days=1)
        past_day_of_week = past_date.strftime('%A').upper()
        
        # Create availability for that day
        DoctorAvailability.objects.create(
            doctor=doctor,
            day_of_week=past_day_of_week,
            start_time=time(9, 0),
            end_time=time(17, 0),
            slot_duration=30
        )
        
        success, result = AppointmentService.book_appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=past_date,
            start_time=time(10, 0),
            notes='Test'
        )
        
        assert success is False
        # The actual error message is capitalized
        assert 'Cannot book appointment in the past' in result or 'past' in result.lower()
    
    def test_cancel_nonexistent_appointment(self, patient):
        """Test canceling non-existent appointment"""
        success, message = AppointmentService.cancel_appointment(
            appointment_id=9999,  # Doesn't exist
            patient=patient
        )
        
        assert success is False
        assert 'not found' in message.lower()
    
    def test_cancel_already_cancelled_appointment(self, patient, doctor):
        """Test canceling already cancelled appointment"""
        future_date = timezone.now().date() + timedelta(days=1)
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=future_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='CANCELLED'  # Already cancelled
        )
        
        success, message = AppointmentService.cancel_appointment(
            appointment_id=appointment.pk,
            patient=patient
        )
        
        assert success is False
        assert 'not found' in message.lower() or 'cannot be cancelled' in message.lower()
    
    @patch('appointments.models.Appointment.save')
    def test_cancel_appointment_save_exception(self, mock_save, patient, doctor):
        """Test cancel_appointment handles save exceptions"""
        future_date = timezone.now().date() + timedelta(days=1)
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=future_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        
        mock_save.side_effect = DatabaseError("Save failed")
        
        success, message = AppointmentService.cancel_appointment(
            appointment_id=appointment.pk,
            patient=patient
        )
        
        assert success is False
    
    def test_modify_nonexistent_appointment(self, patient):
        """Test modifying non-existent appointment"""
        future_date = timezone.now().date() + timedelta(days=1)
        
        success, result = AppointmentService.modify_appointment(
            appointment_id=9999,
            patient=patient,
            new_date=future_date,
            new_time=time(14, 0)
        )
        
        assert success is False
        assert 'not found' in result.lower()
    
    def test_modify_appointment_validation_error(self, patient, doctor):
        """Test modify triggers ValidationError for past date"""
        future_date = timezone.now().date() + timedelta(days=1)
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=future_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        
        past_date = timezone.now().date() - timedelta(days=1)
        
        success, result = AppointmentService.modify_appointment(
            appointment_id=appointment.pk,
            patient=patient,
            new_date=past_date
        )
        
        assert success is False
        assert 'past' in result.lower() or 'cannot' in result.lower()
    
    @patch('appointments.services.Appointment.objects.filter')
    def test_get_appointments_by_doctor_exception(self, mock_filter, doctor):
        """Test get_appointments_by_doctor handles exceptions"""
        mock_filter.side_effect = DatabaseError("DB error")
        
        result = AppointmentService.get_appointments_by_doctor(doctor)
        
        assert result.count() == 0  # Returns empty queryset
    
    @patch('appointments.services.Appointment.objects.filter')
    def test_get_patient_appointments_exception(self, mock_filter, patient):
        """Test get_patient_appointments handles exceptions"""
        mock_filter.side_effect = Exception("Unexpected error")
        
        result = AppointmentService.get_patient_appointments(patient)
        
        assert result.count() == 0


@pytest.mark.django_db
class TestPatientFormServiceExceptions:
    """Test PatientFormService exception handling"""
    
    @patch('appointments.models.PatientForm.objects.create')
    def test_submit_form_database_error(self, mock_create, patient):
        """Test submit_form handles database errors"""
        mock_create.side_effect = DatabaseError("DB error")
        
        success, result = PatientFormService.submit_form(
            patient=patient,
            chief_complaint='Test complaint',
            medical_history='Test history'
        )
        
        assert success is False
        assert 'failed' in result.lower() or 'error' in result.lower()
    
    @patch('appointments.services.PatientForm.objects.filter')
    def test_get_patient_forms_exception(self, mock_filter, patient):
        """Test get_patient_forms handles exceptions"""
        mock_filter.side_effect = Exception("DB connection lost")
        
        result = PatientFormService.get_patient_forms(patient)
        
        assert result.count() == 0


@pytest.mark.django_db
class TestScheduleServiceExceptions:
    """Test ScheduleService exception handling"""
    
    @patch('appointments.models.DoctorAvailability.objects.create')
    def test_update_schedule_database_error(self, mock_create, doctor):
        """Test update_schedule handles database errors"""
        mock_create.side_effect = DatabaseError("DB error")
        
        schedule_data = [{
            'day_of_week': 'MONDAY',
            'start_time': time(9, 0),
            'end_time': time(17, 0),
            'slot_duration': 30
        }]
        
        success, message = ScheduleService.update_schedule(doctor, schedule_data)
        
        assert success is False
        assert 'failed' in message.lower()
    
    def test_update_schedule_empty_data(self, doctor):
        """Test update_schedule with empty schedule data"""
        success, message = ScheduleService.update_schedule(doctor, [])
        
        # Should succeed with 0 slots created
        assert success is True
        assert '0' in message
    
    @patch('appointments.services.DoctorAvailability.objects.filter')
    def test_get_doctor_schedule_exception(self, mock_filter, doctor):
        """Test get_doctor_schedule handles exceptions"""
        mock_filter.side_effect = Exception("DB error")
        
        result = ScheduleService.get_doctor_schedule(doctor)
        
        assert result.count() == 0
