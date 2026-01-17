"""
Tests for ScheduleService success paths.
Exception handling is already covered in appointments/tests/test_service_exceptions.py
"""
import pytest
from datetime import time
from doctors.services import ScheduleService
from doctors.models import DoctorAvailability
from accounts.models import User


@pytest.mark.django_db
class TestScheduleServiceSuccessPaths:
    """Test ScheduleService success scenarios"""
    
    def test_update_schedule_creates_new_availability(self, doctor):
        """Test creating new availability slots"""
        schedule_data = [{
            'day_of_week': 'TUESDAY',
            'start_time': time(9, 0),
            'end_time': time(17, 0),
            'slot_duration': 30,
            'is_active': True
        }]
        
        success, message = ScheduleService.update_schedule(doctor, schedule_data)
        
        assert success is True
        assert '1 availability slot(s)' in message
        
        # Verify created in database
        availability = DoctorAvailability.objects.get(doctor=doctor, day_of_week='TUESDAY')
        assert availability.start_time == time(9, 0)
        assert availability.end_time == time(17, 0)
        assert availability.slot_duration == 30
        assert availability.is_active is True
    
    def test_update_schedule_replaces_existing_availability(self, doctor):
        """Test updating existing day's availability"""
        # Monday already exists from fixture (9:00-17:00)
        assert DoctorAvailability.objects.filter(doctor=doctor, day_of_week='MONDAY').exists()
        
        # Update Monday to different hours
        schedule_data = [{
            'day_of_week': 'MONDAY',
            'start_time': time(10, 0),
            'end_time': time(16, 0),
            'slot_duration': 45,
            'is_active': True
        }]
        
        success, message = ScheduleService.update_schedule(doctor, schedule_data)
        
        assert success is True
        
        # Should only have one Monday entry with new times
        monday_slots = DoctorAvailability.objects.filter(doctor=doctor, day_of_week='MONDAY')
        assert monday_slots.count() == 1
        
        availability = monday_slots.first()
        assert availability.start_time == time(10, 0)
        assert availability.end_time == time(16, 0)
        assert availability.slot_duration == 45
    
    def test_update_schedule_multiple_days(self, doctor):
        """Test creating availability for multiple days"""
        schedule_data = [
            {
                'day_of_week': 'WEDNESDAY',
                'start_time': time(8, 0),
                'end_time': time(14, 0),
                'slot_duration': 20
            },
            {
                'day_of_week': 'THURSDAY',
                'start_time': time(13, 0),
                'end_time': time(19, 0),
                'slot_duration': 40
            },
            {
                'day_of_week': 'FRIDAY',
                'start_time': time(9, 0),
                'end_time': time(12, 0),
                'slot_duration': 30
            }
        ]
        
        success, message = ScheduleService.update_schedule(doctor, schedule_data)
        
        assert success is True
        assert '3 availability slot(s)' in message
        
        # Verify all three days created
        assert DoctorAvailability.objects.filter(doctor=doctor, day_of_week='WEDNESDAY').exists()
        assert DoctorAvailability.objects.filter(doctor=doctor, day_of_week='THURSDAY').exists()
        assert DoctorAvailability.objects.filter(doctor=doctor, day_of_week='FRIDAY').exists()
    
    def test_update_schedule_with_default_values(self, doctor):
        """Test schedule creation uses default values when not provided"""
        schedule_data = [{
            'day_of_week': 'SATURDAY',
            'start_time': time(10, 0),
            'end_time': time(14, 0)
            # slot_duration and is_active not provided
        }]
        
        success, message = ScheduleService.update_schedule(doctor, schedule_data)
        
        assert success is True
        
        availability = DoctorAvailability.objects.get(doctor=doctor, day_of_week='SATURDAY')
        assert availability.slot_duration == 30  # Default
        assert availability.is_active is True  # Default
    
    def test_get_doctor_schedule_returns_all_slots(self, doctor):
        """Test retrieving doctor's full schedule"""
        # Create additional availability
        DoctorAvailability.objects.create(
            doctor=doctor,
            day_of_week='WEDNESDAY',
            start_time=time(9, 0),
            end_time=time(17, 0),
            slot_duration=30
        )
        
        schedule = ScheduleService.get_doctor_schedule(doctor)
        
        # Should have Monday (from fixture) and Wednesday
        assert schedule.count() == 2
        days = [slot.day_of_week for slot in schedule]
        assert 'MONDAY' in days
        assert 'WEDNESDAY' in days
    
    def test_get_doctor_schedule_ordered_by_day(self, doctor):
        """Test schedule is ordered correctly by day of week"""
        # Create multiple days
        DoctorAvailability.objects.create(
            doctor=doctor,
            day_of_week='FRIDAY',
            start_time=time(9, 0),
            end_time=time(17, 0),
            slot_duration=30
        )
        DoctorAvailability.objects.create(
            doctor=doctor,
            day_of_week='TUESDAY',
            start_time=time(9, 0),
            end_time=time(17, 0),
            slot_duration=30
        )
        
        schedule = ScheduleService.get_doctor_schedule(doctor)
        
        # Should be ordered by day_of_week field
        days = [slot.day_of_week for slot in schedule]
        assert days == sorted(days)
    
    def test_get_doctor_schedule_empty_for_new_doctor(self, db):
        """Test empty schedule for doctor with no availability"""
        # Create a new doctor without availability
        user = User.objects.create_user(
            email='newdoc@example.com',
            password='password123',
            first_name='New',
            last_name='Doctor',
            date_of_birth='1985-01-01',
            role='DOCTOR',
            phone='0931234567'
        )
        from doctors.models import Doctor
        new_doctor = Doctor.objects.create(
            user=user,
            specialization='GENERAL',
            license_number='NEW123'
        )
        
        schedule = ScheduleService.get_doctor_schedule(new_doctor)
        
        assert schedule.count() == 0
