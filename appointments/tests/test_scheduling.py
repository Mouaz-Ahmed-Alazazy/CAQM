import pytest
from django.urls import reverse
from appointments.models import DoctorAvailability
from datetime import time

@pytest.mark.django_db
class TestScheduling:
    
    def test_update_availability(self, authenticated_doctor_client, doctor):
        """Test doctor updating their availability"""
        url = reverse('appointments:availability_management')
        
        # Add availability for Tuesday
        data = {
            'availability_form': '1', # Trigger POST
            'day_of_week': 'TUESDAY',
            'start_time': '09:00',
            'end_time': '17:00',
            'slot_duration': 30,
            'is_active': 'on'
        }
        
        response = authenticated_doctor_client.post(url, data)
        
        assert response.status_code == 302
        assert response.url == reverse('appointments:availability_management')
        
        # Check if Tuesday availability is created
        assert DoctorAvailability.objects.filter(doctor=doctor, day_of_week='TUESDAY').exists()
        avail = DoctorAvailability.objects.get(doctor=doctor, day_of_week='TUESDAY')
        assert avail.start_time == time(9, 0)
        assert avail.end_time == time(17, 0)

    def test_delete_availability(self, authenticated_doctor_client, doctor):
        """Test deleting availability"""
        # Ensure Monday exists (from fixture)
        monday_avail = DoctorAvailability.objects.get(doctor=doctor, day_of_week='MONDAY')
        
        url = reverse('appointments:delete_availability', args=[monday_avail.id])
        
        response = authenticated_doctor_client.get(url)
        
        assert response.status_code == 302
        assert response.url == reverse('appointments:availability_management')
        
        assert not DoctorAvailability.objects.filter(id=monday_avail.id).exists()

    def test_view_availability_management(self, authenticated_doctor_client, doctor):
        """Test viewing the availability management page"""
        url = reverse('appointments:availability_management')
        response = authenticated_doctor_client.get(url)
        
        assert response.status_code == 200
        assert 'availabilities' in response.context
        assert 'form' in response.context
