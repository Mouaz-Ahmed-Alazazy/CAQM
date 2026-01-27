import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import time
from appointments.models import Appointment
from doctors.models import DoctorAvailability, Doctor
from django.contrib.auth import get_user_model
import uuid

@pytest.mark.django_db
class TestViewingPerformance:
    
    def test_home_page_query_count(self, authenticated_patient_client, django_assert_num_queries, doctor):
        """Test that query count is reasonable"""
        
        # Add availability to the default doctor
        DoctorAvailability.objects.update_or_create(
            doctor=doctor, day_of_week='MONDAY', 
            defaults={'start_time': time(9,0), 'end_time': time(17,0)}
        )
        
        # Create another doctor with availability
        User = get_user_model()
        u2 = User.objects.create_user(
            email=f'doc2_{uuid.uuid4()}@example.com', 
            password='password', 
            role='DOCTOR',
            first_name='Doc',
            last_name='Two',
            date_of_birth='1980-01-01',
            gender='MALE'
        )
        d2 = Doctor.objects.create(user=u2, specialization='DERMATOLOGY')
        DoctorAvailability.objects.create(
            doctor=d2, day_of_week='TUESDAY', start_time=time(9,0), end_time=time(17,0)
        )
        
        url = reverse('patients:home')
        
        # Ensure only a fixed number of queries are executed even with multiple doctors/availabilities
        # 1. Session 2. User 3. Doctors (prefetch) 4. Availabilities (prefetch) 5. Patient Profile (maybe)
        # We allow a buffer for auth/session overhead but ensure it's not proportional to doctors loop
        with django_assert_num_queries(4): 
             response = authenticated_patient_client.get(url)
             
        assert response.status_code == 200
