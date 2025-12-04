import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime
from appointments.models import Appointment

@pytest.mark.django_db
class TestBookingAppointment:
    
    def test_book_appointment_success(self, authenticated_patient_client, doctor, patient):
        """Test successful appointment booking"""
        # Find next Monday
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0: # Target next week if today is Monday or later
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        
        url = reverse('appointments:book_appointment')
        data = {
            'doctor': doctor.pk,
            'appointment_date': next_monday,
            'start_time': '09:00', # Assuming 9:00 is available as per fixture
            'notes': 'Test appointment'
        }
        
        response = authenticated_patient_client.post(url, data)
        
        # Should redirect to my_appointments
        assert response.status_code == 302
        assert response.url == reverse('appointments:my_appointments')
        
        # Verify appointment created
        assert Appointment.objects.count() == 1
        appointment = Appointment.objects.first()
        assert appointment.patient == patient
        assert appointment.doctor == doctor
        assert appointment.appointment_date == next_monday
        assert appointment.start_time.strftime('%H:%M') == '09:00'
        assert appointment.status == 'SCHEDULED'

    def test_book_appointment_past_date(self, authenticated_patient_client, doctor):
        """Test booking with a past date"""
        past_date = timezone.now().date() - timedelta(days=1)
        url = reverse('appointments:book_appointment')
        data = {
            'doctor': doctor.pk,
            'appointment_date': past_date,
            'start_time': '09:00',
            'notes': 'Past appointment'
        }
        
        response = authenticated_patient_client.post(url, data)
        
        # Should stay on page with error
        assert response.status_code == 200
        assert Appointment.objects.count() == 0


    def test_get_available_slots(self, authenticated_patient_client, doctor):
        """Test AJAX view for available slots"""
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        
        url = reverse('appointments:get_available_slots')
        response = authenticated_patient_client.get(url, {
            'doctor_id': doctor.pk,
            'date': next_monday.strftime('%Y-%m-%d')
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'slots' in data
        assert len(data['slots']) > 0
        # Check if 09:00 is in slots
        times = [slot['time'] for slot in data['slots']]
        assert '09:00' in times

    def test_book_appointment_doctor_unavailable(self, authenticated_patient_client, doctor, patient):
        """Test booking on a day doctor is not available (e.g., Sunday)"""
        today = timezone.now().date()
        days_ahead = 6 - today.weekday() # Sunday
        if days_ahead <= 0:
            days_ahead += 7
        next_sunday = today + timedelta(days=days_ahead)
        
        url = reverse('appointments:book_appointment')
        data = {
            'doctor': doctor.pk,
            'appointment_date': next_sunday,
            'start_time': '09:00',
            'notes': 'Sunday appointment'
        }
        
        response = authenticated_patient_client.post(url, data)
        
        assert response.status_code == 200 # Form invalid
        assert Appointment.objects.count() == 0
