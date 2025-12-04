import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time
from appointments.models import Appointment, PatientForm

@pytest.mark.django_db
class TestAdditionalCoverage:
    
    def test_patient_form_submission_success(self, authenticated_patient_client, patient):
        """Test submitting a patient medical form"""
        url = reverse('appointments:submit_patient_form')
        data = {
            'chief_complaint': 'Chest pain',
            'medical_history': 'Hypertension',
            'current_medications': 'Aspirin',
            'allergies': 'Penicillin'
        }
        
        response = authenticated_patient_client.post(url, data)
        
        assert response.status_code == 302
        assert response.url == reverse('appointments:my_appointments')
        
        # Verify form created
        assert PatientForm.objects.filter(patient=patient).exists()
        form = PatientForm.objects.get(patient=patient)
        assert form.chief_complaint == 'Chest pain'
        assert form.medical_history == 'Hypertension'

    def test_patient_form_submission_missing_chief_complaint(self, authenticated_patient_client, patient):
        """Test form submission without required chief complaint"""
        url = reverse('appointments:submit_patient_form')
        data = {
            'chief_complaint': '',
            'medical_history': 'None',
        }
        
        response = authenticated_patient_client.post(url, data)
        
        # Should render form again with error
        assert response.status_code == 200
        assert PatientForm.objects.count() == 0

    def test_patient_form_get_view(self, authenticated_patient_client, patient):
        """Test GET request to patient form view"""
        url = reverse('appointments:submit_patient_form')
        response = authenticated_patient_client.get(url)
        
        assert response.status_code == 200
        assert 'patient_form' in response.context

    def test_my_appointments_view_with_past_appointments(self, authenticated_patient_client, patient, doctor):
        """Test viewing appointments including past ones"""
        today = timezone.now().date()
        
        # Create appointment in future first, then update to past to bypass validation
        future_date = today + timedelta(days=5)
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=future_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        
        # Update to past date and completed status using queryset update (bypasses model validation)
        Appointment.objects.filter(pk=appointment.pk).update(
            appointment_date=today - timedelta(days=5),
            status='COMPLETED'
        )
        
        url = reverse('appointments:my_appointments')
        response = authenticated_patient_client.get(url)
        
        assert response.status_code == 200
        assert 'past_appointments' in response.context
        assert len(response.context['past_appointments']) == 1

    def test_doctor_dashboard_view(self, authenticated_doctor_client, doctor):
        """Test doctor dashboard view"""
        url = reverse('appointments:doctor_dashboard')
        response = authenticated_doctor_client.get(url)
        
        assert response.status_code == 200
        assert 'doctor' in response.context
        assert 'availabilities' in response.context
        assert 'upcoming_appointments' in response.context
        assert 'today_appointments' in response.context
        assert 'form' in response.context

    def test_doctor_dashboard_post_availability(self, authenticated_doctor_client, doctor):
        """Test posting availability from doctor dashboard"""
        url = reverse('appointments:doctor_dashboard')
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
        assert response.url == reverse('appointments:doctor_dashboard')

    def test_get_available_slots_no_params(self, authenticated_patient_client):
        """Test available slots endpoint without parameters"""
        url = reverse('appointments:get_available_slots')
        response = authenticated_patient_client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert data['slots'] == []

    def test_get_available_slots_invalid_date(self, authenticated_patient_client, doctor):
        """Test available slots with invalid date format"""
        url = reverse('appointments:get_available_slots')
        response = authenticated_patient_client.get(url, {
            'doctor_id': doctor.pk,
            'date': 'invalid-date'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'error' in data or data['slots'] == []

    def test_modify_appointment_get_view(self, authenticated_patient_client, patient, doctor):
        """Test GET request to modify appointment view"""
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )
        
        url = reverse('appointments:modify_appointment', args=[appointment.pk])
        response = authenticated_patient_client.get(url)
        
        assert response.status_code == 200
        assert 'appointment' in response.context
        assert 'doctor' in response.context

    def test_book_appointment_get_view(self, authenticated_patient_client):
        """Test GET request to book appointment view"""
        url = reverse('appointments:book_appointment')
        response = authenticated_patient_client.get(url)
        
        assert response.status_code == 200
        assert 'doctors' in response.context
        assert 'form' in response.context
