import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time
from appointments.models import Appointment

@pytest.mark.django_db
class TestViewingAppointments:
    
    @pytest.fixture
    def appointments(self, patient, doctor):
        today = timezone.now().date()
        
        # Today's appointment
        app1 = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=today,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED',
            notes='Test notes'
        )
        
        # Upcoming appointment (tomorrow)
        app2 = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=today + timedelta(days=1),
            start_time=time(11, 0),
            end_time=time(11, 30),
            status='SCHEDULED',
            notes='Test notes'
        )
        
        return [app1, app2]

    def test_patient_view_appointments(self, authenticated_patient_client, appointments):
        """Test patient viewing their appointments"""
        url = reverse('appointments:my_appointments')
        response = authenticated_patient_client.get(url)
        
        assert response.status_code == 200
        assert 'upcoming_appointments' in response.context
        # Should see both (if today is >= today)
        upcoming = response.context['upcoming_appointments']
        assert len(upcoming) == 2

    def test_doctor_view_today(self, authenticated_doctor_client, appointments):
        """Test doctor viewing today's appointments"""
        url = reverse('appointments:today_appointments')
        response = authenticated_doctor_client.get(url)
        
        assert response.status_code == 200
        assert 'today_appointments' in response.context
        today_apps = response.context['today_appointments']
        assert len(today_apps) == 1
        assert today_apps[0].pk == appointments[0].pk

    def test_doctor_view_upcoming(self, authenticated_doctor_client, appointments):
        """Test doctor viewing upcoming appointments"""
        url = reverse('appointments:upcoming_appointments')
        response = authenticated_doctor_client.get(url)
        
        assert response.status_code == 200
        assert 'upcoming_appointments' in response.context
        upcoming_apps = response.context['upcoming_appointments']
        assert len(upcoming_apps) == 1
        assert upcoming_apps[0].pk == appointments[1].pk
