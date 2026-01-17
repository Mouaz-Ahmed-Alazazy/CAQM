"""
Tests for Doctor model methods and business logic.
"""
import pytest
from django.utils import timezone
from datetime import time, timedelta
from doctors.models import Doctor, DoctorAvailability
from appointments.models import Appointment
from patients.models import Patient
from accounts.models import User


@pytest.mark.django_db
class TestDoctorModel:
    """Test Doctor model methods"""
    
    def test_get_available_slots_for_date_with_availability(self, doctor):
        """Test slot generation for a day with availability"""
        # Monday availability already created in fixture (9:00-17:00, 30 min slots)
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()  # 0 = Monday
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        
        slots = doctor.get_available_slots_for_date(next_monday)
        
        # Should have 15 slots (9:00-17:00 in 30-min intervals)
        # 9:00, 9:30, 10:00, ..., 16:00 (last slot that fits before 17:00)
        # Limited to 15 slots max per day
        assert len(slots) == 15
        assert time(9, 0) in slots
        assert time(16, 0) in slots
        assert time(17, 0) not in slots  # End time not included
    
    def test_get_available_slots_for_date_no_availability(self, doctor):
        """Test returns empty list when doctor not available on that day"""
        # Get a Tuesday (no availability in fixture)
        today = timezone.now().date()
        days_ahead = 1 - today.weekday()  # 1 = Tuesday
        if days_ahead <= 0:
            days_ahead += 7
        next_tuesday = today + timedelta(days=days_ahead)
        
        slots = doctor.get_available_slots_for_date(next_tuesday)
        
        assert slots == []
    
    def test_get_available_slots_excludes_booked_slots(self, doctor, patient):
        """Test booked slots are filtered out"""
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        
        # Book 10:00 slot
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        
        slots = doctor.get_available_slots_for_date(next_monday)
        
        # 10:00 should not be in available slots
        assert time(10, 0) not in slots
        # But 9:00 and 10:30 should still be available
        assert time(9, 0) in slots
        assert time(10, 30) in slots
    
    def test_get_available_slots_respects_max_15_appointments(self, doctor, db):
        """Test 15 appointment limit per day"""
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        
        # Create 15 appointments with different patients to avoid validation error
        for i in range(15):
            # Create a unique patient for each appointment
            user = User.objects.create_user(
                email=f'patient{i}@example.com',
                password='password123',
                first_name=f'Patient{i}',
                last_name='Test',
                date_of_birth='1990-01-01',
                role='PATIENT',
                phone=f'091{i:07d}'
            )
            patient_i = Patient.objects.create(
                user=user,
                address=f'{i} Test St'
            )
            
            hour = 9 + (i // 2)
            minute = (i % 2) * 30
            end_minute = minute + 30
            end_hour = hour
            if end_minute >= 60:
                end_minute -= 60
                end_hour += 1
            
            Appointment.objects.create(
                patient=patient_i,
                doctor=doctor,
                appointment_date=next_monday,
                start_time=time(hour, minute),
                end_time=time(end_hour, end_minute),
                status='SCHEDULED'
            )
        
        slots = doctor.get_available_slots_for_date(next_monday)
        
        # Should return empty list when 15 appointments reached
        assert slots == []
    
    def test_get_available_slots_excludes_checked_in_appointments(self, doctor, patient):
        """Test CHECKED_IN appointments also count as booked"""
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        
        # Create CHECKED_IN appointment
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(11, 0),
            end_time=time(11, 30),
            status='CHECKED_IN'
        )
        
        slots = doctor.get_available_slots_for_date(next_monday)
        
        # 11:00 should not be available
        assert time(11, 0) not in slots
    
    def test_doctor_str_method(self, doctor):
        """Test string representation of Doctor"""
        expected = f"Dr. {doctor.user.get_full_name()} - Cardiology"
        assert str(doctor) == expected
    
    def test_doctor_specialization_choices(self):
        """Test all specialization options are valid"""
        valid_specializations = [
            'CARDIOLOGY', 'DERMATOLOGY', 'NEUROLOGY', 
            'ORTHOPEDICS', 'PEDIATRICS', 'PSYCHIATRY', 'GENERAL'
        ]
        
        # Get choices from model
        choices = [choice[0] for choice in Doctor.SPECIALIZATION_CHOICES]
        
        for spec in valid_specializations:
            assert spec in choices
