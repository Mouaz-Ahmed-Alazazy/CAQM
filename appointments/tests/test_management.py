import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time
from appointments.models import Appointment

@pytest.mark.django_db
class TestAppointmentManagement:
    
    @pytest.fixture
    def appointment(self, patient, doctor):
        # Create an appointment for next Monday 10:00
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        
        return Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=next_monday,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='SCHEDULED'
        )

    def test_modify_appointment_success(self, authenticated_patient_client, appointment):
        """Test modifying an appointment"""
        url = reverse('appointments:modify_appointment', args=[appointment.pk])
        
        # Change time to 11:00 (assuming it's available)
        new_time = '11:00'
        data = {
            'appointment_date': appointment.appointment_date.strftime('%Y-%m-%d'),
            'start_time': new_time,
            'notes': 'Modified note'
        }
        
        response = authenticated_patient_client.post(url, data)
        
        assert response.status_code == 302
        assert response.url == reverse('appointments:my_appointments')
        
        appointment.refresh_from_db()
        assert appointment.start_time.strftime('%H:%M') == new_time
        assert appointment.notes == 'Modified note'

    def test_cancel_appointment_success(self, authenticated_patient_client, appointment):
        """Test cancelling an appointment"""
        url = reverse('appointments:cancel_appointment', args=[appointment.pk])
        
        response = authenticated_patient_client.post(url)
        
        assert response.status_code == 302
        assert response.url == reverse('appointments:my_appointments')
        
        appointment.refresh_from_db()
        assert appointment.status == 'CANCELLED'

    def test_modify_appointment_not_owner(self, client, appointment, doctor_user):
        """Test that another user cannot modify the appointment"""
        # Login as doctor (who is not the patient owner)
        client.force_login(doctor_user)
        url = reverse('appointments:modify_appointment', args=[appointment.pk])
        
        # PatientRequiredMixin should redirect to login or show error (403/302)
        # The mixin redirects to login if not patient, but here doctor is logged in.
        # PatientRequiredMixin checks is_patient(). Doctor is not patient.
        # So it should redirect to login with error message.
        
        response = client.get(url)
        assert response.status_code == 302 # Redirects to login


@pytest.mark.django_db
class TestBulkCancellation:
    """Test bulk appointment cancellation edge cases (lines 212-225)"""
    
    def test_bulk_cancel_no_appointments_selected(self, authenticated_patient_client):
        """Test bulk cancel with no appointment IDs selected"""
        url = reverse('appointments:my_appointments')
        
        # POST with empty list
        response = authenticated_patient_client.post(url, {})
        
        assert response.status_code == 302
        assert response.url == reverse('appointments:my_appointments')
    
    def test_bulk_cancel_already_cancelled_appointments(self, authenticated_patient_client, patient, doctor):
        """Test bulk cancel with already cancelled appointments (no action)"""
        future_date = timezone.now().date() + timedelta(days=1)
        
        # Create cancelled appointment
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=future_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='CANCELLED'  # Already cancelled
        )
        
        url = reverse('appointments:my_appointments')
        data = {'appointment_ids': [appointment.pk]}
        
        response = authenticated_patient_client.post(url, data)
        
        assert response.status_code == 302
        # Should show warning: "No appointments were cancelled"
        from django.contrib.messages import get_messages
        messages = list(get_messages(response.wsgi_request))
        assert any('No appointments' in str(m) or 'warning' in str(m).lower() for m in messages)
    
    def test_bulk_cancel_multiple_appointments(self, authenticated_patient_client, patient, doctor):
        """Test bulk cancelling multiple appointments successfully"""
        future_date = timezone.now().date() + timedelta(days=5)  # Use different date
        
        # Create 3 scheduled appointments on different dates to avoid validation error
        appointments = []
        for i in range(3):
            app = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=future_date + timedelta(days=i), # Different dates
                start_time=time(10, 0),
                end_time=time(10, 30),
                status='SCHEDULED'
            )
            appointments.append(app)
        
        url = reverse('appointments:my_appointments')
        data = {'appointment_ids': [app.pk for app in appointments]}
        
        response = authenticated_patient_client.post(url, data)
        
        assert response.status_code == 302
        
        # Check message
        from django.contrib.messages import get_messages
        messages = list(get_messages(response.wsgi_request))
        assert any('3 appointment(s) cancelled' in str(m) for m in messages)
        
        # Verify all are cancelled
        for app in appointments:
            app.refresh_from_db()
            assert app.status == 'CANCELLED'
