import pytest
from django.utils import timezone
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'caqm_project.settings')
django.setup()

from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor, DoctorAvailability
from appointments.models import Appointment
from queues.models import Queue, PatientQueue
from admins.services import AdminBookingService

@pytest.mark.django_db
def test_debug():
    admin = User.objects.create_superuser(email="admin_book@test.com", password="pwd", role="ADMIN")
    doctor_user = User.objects.create_user(email="doc_book@test.com", password="pwd", role="DOCTOR")
    doctor = Doctor.objects.create(user=doctor_user)
    patient_user = User.objects.create_user(email="pt_book@test.com", password="pwd", role="PATIENT")
    patient = Patient.objects.create(user=patient_user)
    today = timezone.localtime().date()
    DoctorAvailability.objects.create(doctor=doctor, day_of_week=today.strftime("%A").upper(), start_time="09:00", end_time="17:00", slot_duration=30, is_active=True)

    q = Queue.objects.create(doctor=doctor, date=today)
    pq = PatientQueue.objects.create(queue=q, patient=patient, position=10, status="WAITING")

    # Add a second patient queue
    patient_user2 = User.objects.create_user(email="pt2@test.com", password="pwd", role="PATIENT")
    patient2 = Patient.objects.create(user=patient_user2)
    pq2 = PatientQueue.objects.create(queue=q, patient=patient2, status="WAITING")

    success, result = AdminBookingService.book_emergency_appointment(patient.pk, doctor.pk, notes="Urgent now", booked_by=admin)
    print("Success:", success)
    
    pq.refresh_from_db()
    print("PQ1:", pq.status, pq.position, pq.is_emergency)
    pq2.refresh_from_db()
    print("PQ2:", pq2.status, pq2.position, pq2.is_emergency)

