import pytest
from django.utils import timezone
from django.urls import reverse
from appointments.models import Appointment
from queues.models import Queue, PatientQueue
from doctors.models import Doctor
from patients.models import Patient
from accounts.models import User

@pytest.mark.django_db
class TestDoctorCheckInGuard:
    @pytest.fixture
    def setup_data(self, db):
        # Create doctor
        doctor_user = User.objects.create_user(
            email='doctor@example.com', 
            password='password', 
            role='DOCTOR',
            first_name='John',
            last_name='Doe',
            date_of_birth='1980-01-01',
            gender='MALE'
        )
        doctor = Doctor.objects.create(user=doctor_user, specialization='GENERAL')
        
        # Create patient
        patient_user = User.objects.create_user(
            email='patient@example.com', 
            password='password', 
            role='PATIENT',
            first_name='Jane',
            last_name='Smith',
            date_of_birth='1990-01-01',
            gender='FEMALE'
        )
        patient = Patient.objects.create(user=patient_user)
        
        # Create appointment for today
        today = timezone.now().date()
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=today,
            start_time='10:00:00',
            end_time='10:30:00',
            status='SCHEDULED'
        )
        
        # Create queue
        queue = Queue.objects.create(doctor=doctor, date=today)
        
        # Add patient to queue
        pq = PatientQueue.objects.create(
            queue=queue,
            patient=patient,
            position=1,
            status='WAITING'
        )
        
        return {
            'doctor': doctor,
            'patient': patient,
            'appointment': appointment,
            'queue': queue,
            'pq': pq,
            'doctor_user': doctor_user
        }

    def test_call_next_blocked_before_doctor_checkin(self, client, setup_data):
        """Nurse/API cannot call next patient if doctor hasn't checked in."""
        client.login(email='doctor@example.com', password='password')
        url = reverse('queues:call_next_patient')
        
        response = client.post(url, {'queue_id': setup_data['queue'].pk})
        
        assert response.status_code == 400
        assert response.json()['success'] is False
        assert response.json()['message'] == "Doctor hasn't checked in yet."
        
        # Verify status remained WAITING
        setup_data['pq'].refresh_from_db()
        assert setup_data['pq'].status == 'WAITING'

    def test_call_next_succeeds_after_doctor_checkin(self, client, setup_data):
        """Nurse/API can call next after doctor has checked in (via appointment status)."""
        # Manually set appointment to CHECKED_IN to simulate doctor check-in
        setup_data['appointment'].status = 'CHECKED_IN'
        setup_data['appointment'].save()
        
        client.login(email='doctor@example.com', password='password')
        url = reverse('queues:call_next_patient')
        
        response = client.post(url, {'queue_id': setup_data['queue'].pk})
        
        assert response.status_code == 200
        assert response.json()['success'] is True
        
        # Verify status updated to IN_PROGRESS
        setup_data['pq'].refresh_from_db()
        assert setup_data['pq'].status == 'IN_PROGRESS'
        assert setup_data['pq'].consultation_start_time is not None

    def test_doctor_qr_checkin_updates_appointments(self, client, setup_data):
        """Doctor QR scan check-in updates scheduled appointments to CHECKED_IN."""
        from queues.services import CheckInService
        
        # Use the service directly to simulate QR scan processing
        qr_data = f"QUEUE-{setup_data['doctor'].pk}-{timezone.now().strftime('%Y%m%d')}"
        result = CheckInService.process_check_in(setup_data['doctor_user'], qr_data)
        
        assert result['success'] is True
        
        # Verify appointment updated
        setup_data['appointment'].refresh_from_db()
        assert setup_data['appointment'].status == 'CHECKED_IN'
        
        # Verify guard now allows calling next patient
        url = reverse('queues:call_next_patient')
        client.login(email='doctor@example.com', password='password')
        response = client.post(url, {'queue_id': setup_data['queue'].pk})
        assert response.status_code == 200
        assert response.json()['success'] is True
