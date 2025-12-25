
import pytest
from django.urls import reverse
from django.utils import timezone
from appointments.models import Appointment

@pytest.mark.django_db
class TestAdditionalCoverage:

    def test_doctor_dashboard_view(self, authenticated_doctor_client, doctor):
        """Test doctor dashboard view"""
        url = reverse('doctors:doctor_dashboard')
        response = authenticated_doctor_client.get(url)
        
        assert response.status_code == 200
        assert 'doctor' in response.context
        assert 'availabilities' in response.context
        assert 'upcoming_appointments' in response.context
        assert 'today_appointments' in response.context
        assert 'form' in response.context

    def test_doctor_dashboard_post_availability(self, authenticated_doctor_client, doctor):
        """Test posting availability from doctor dashboard"""
        url = reverse('doctors:doctor_dashboard')
        data = {
            'availability_form': '1',
            'day_of_week': 'WEDNESDAY',
            'start_time': '08:00',
            'end_time': '16:00',
            'slot_duration': 30,
            'is_active': 'on'
        }
        
        response = authenticated_doctor_client.post(url, data)
        
        assert response.status_code == 302
        assert response.url == reverse('doctors:doctor_dashboard')
