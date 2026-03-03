import datetime
import pytest
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor, DoctorAvailability
from appointments.models import Appointment
from queues.models import Queue, PatientQueue
from admins.services import AdminBookingService


@pytest.mark.django_db
class TestAdminBookingService:
    @pytest.fixture
    def setup_data(self):
        admin = User.objects.create_superuser(
            email="admin_book@test.com", password="pwd", role="ADMIN"
        )

        doctor_user = User.objects.create_user(
            email="doc_book@test.com", password="pwd", role="DOCTOR"
        )
        doctor = Doctor.objects.create(user=doctor_user)

        patient_user = User.objects.create_user(
            email="pt_book@test.com", password="pwd", role="PATIENT"
        )
        patient = Patient.objects.create(user=patient_user)

        today = timezone.now().date()

        # Add availability so appointment booking succeeds
        DoctorAvailability.objects.create(
            doctor=doctor,
            day_of_week=today.strftime("%A").upper(),
            start_time="09:00",
            end_time="17:00",
            slot_duration=30,
            is_active=True,
        )

        return {"admin": admin, "doctor": doctor, "patient": patient, "today": today}

    def test_book_appointment_success(self, setup_data):
        success, result = AdminBookingService.book_appointment(
            setup_data["patient"].pk,
            setup_data["doctor"].pk,
            setup_data["today"],
            datetime.time(10, 0),
            notes="Regular checkup",
            booked_by=setup_data["admin"],
        )
        assert success
        assert result.status == "SCHEDULED"
        assert result.booked_by == setup_data["admin"]

    def test_book_appointment_patient_not_found(self, setup_data):
        success, msg = AdminBookingService.book_appointment(
            9999, setup_data["doctor"].pk, setup_data["today"], datetime.time(10, 0)
        )
        assert not success
        assert "Patient not found" in msg

    def test_book_appointment_doctor_not_found(self, setup_data):
        success, msg = AdminBookingService.book_appointment(
            setup_data["patient"].pk, 9999, setup_data["today"], datetime.time(10, 0)
        )
        assert not success
        assert "Doctor not found" in msg

    @patch("appointments.services.AppointmentService.book_appointment")
    def test_book_appointment_service_failure(self, mock_book, setup_data):
        # Mock AppointmentService failure
        mock_book.return_value = (False, "outside doctor's availability")
        success, msg = AdminBookingService.book_appointment(
            setup_data["patient"].pk,
            setup_data["doctor"].pk,
            setup_data["today"],
            datetime.time(18, 0),
        )
        assert not success
        assert "outside doctor's availability" in msg.lower()

    @patch("appointments.services.AppointmentService.book_appointment")
    def test_book_appointment_exception(self, mock_book, setup_data):
        mock_book.side_effect = Exception("DB error")
        success, msg = AdminBookingService.book_appointment(
            setup_data["patient"].pk,
            setup_data["doctor"].pk,
            setup_data["today"],
            datetime.time(10, 0),
        )
        assert not success
        assert "DB error" in msg

    def test_book_emergency_appointment_success(self, setup_data):
        success, result = AdminBookingService.book_emergency_appointment(
            setup_data["patient"].pk,
            setup_data["doctor"].pk,
            notes="Heart attack",
            booked_by=setup_data["admin"],
        )
        assert success
        assert result["appointment"].status == "CHECKED_IN"
        assert "[EMERGENCY]" in result["appointment"].notes
        assert result["appointment"].booked_by == setup_data["admin"]
        assert result["patient_queue"].status == "EMERGENCY"
        assert result["patient_queue"].is_emergency

    def test_book_emergency_existing_queue(self, setup_data):
        q = Queue.objects.create(doctor=setup_data["doctor"], date=setup_data["today"])
        pq = PatientQueue.objects.create(
            queue=q, patient=setup_data["patient"], position=10, status="WAITING"
        )

        success, result = AdminBookingService.book_emergency_appointment(
            setup_data["patient"].pk, setup_data["doctor"].pk, notes="Urgent now"
        )
        assert success
        pq.refresh_from_db()
        assert pq.position == 1
        assert pq.status == "EMERGENCY"

    def test_book_emergency_not_found(self, setup_data):
        success, msg = AdminBookingService.book_emergency_appointment(
            9999, setup_data["doctor"].pk
        )
        assert not success
        assert "Patient not found" in msg

        success, msg = AdminBookingService.book_emergency_appointment(
            setup_data["patient"].pk, 9999
        )
        assert not success
        assert "Doctor not found" in msg

    @patch("appointments.models.Appointment.objects.create")
    def test_book_emergency_exception(self, mock_create, setup_data):
        mock_create.side_effect = Exception("DB error")
        success, msg = AdminBookingService.book_emergency_appointment(
            setup_data["patient"].pk, setup_data["doctor"].pk
        )
        assert not success
        assert "DB error" in msg
