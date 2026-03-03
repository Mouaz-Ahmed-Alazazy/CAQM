import pytest
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor, DoctorAvailability
from appointments.models import Appointment
from accounts.models import Notification
from admins.services import AdminAppointmentService


@pytest.mark.django_db
class TestAdminAppointmentService:
    @pytest.fixture
    def setup_data(self):
        doctor_user = User.objects.create_user(
            email="doc1@test.com",
            password="pwd",
            role="DOCTOR",
            first_name="John",
            last_name="Doe",
        )
        doctor = Doctor.objects.create(user=doctor_user, specialization="CARDIOLOGY")

        patient_user = User.objects.create_user(
            email="pt1@test.com",
            password="pwd",
            role="PATIENT",
            first_name="Jane",
            last_name="Smith",
        )
        patient = Patient.objects.create(user=patient_user)

        today = timezone.localtime().date()

        appt1 = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=today + timedelta(days=1),
            start_time="10:00:00",
            end_time="10:30:00",
            status="SCHEDULED",
        )

        return {"doctor": doctor, "patient": patient, "appt1": appt1, "today": today}

    def test_get_appointments(self, setup_data):
        doc = setup_data["doctor"]
        today = setup_data["today"]

        # Another appt
        Appointment.objects.create(
            patient=setup_data["patient"],
            doctor=doc,
            appointment_date=today + timedelta(days=5),
            start_time="11:00:00",
            end_time="11:30:00",
            status="COMPLETED",
        )

        appts = AdminAppointmentService.get_appointments()
        assert appts.count() == 2

        assert AdminAppointmentService.get_appointments(doctor_id=doc.pk).count() == 2
        assert (
            AdminAppointmentService.get_appointments(
                date_from=today + timedelta(days=2)
            ).count()
            == 1
        )
        assert (
            AdminAppointmentService.get_appointments(
                date_to=today + timedelta(days=2)
            ).count()
            == 1
        )
        assert AdminAppointmentService.get_appointments(status="COMPLETED").count() == 1

    def test_cancel_single_appointment_already_cancelled(self, setup_data):
        appt = setup_data["appt1"]
        appt.status = "CANCELLED"
        appt.save()

        success, msg = AdminAppointmentService.cancel_single_appointment(appt.pk)
        assert not success
        assert "already cancelled" in msg

    def test_cancel_single_appointment_completed(self, setup_data):
        appt = setup_data["appt1"]
        appt.status = "COMPLETED"
        appt.save()

        success, msg = AdminAppointmentService.cancel_single_appointment(appt.pk)
        assert not success
        assert "Cannot cancel a completed" in msg

    def test_cancel_single_appointment_past(self, setup_data):
        appt = setup_data["appt1"]
        past_date = timezone.now().date() - timedelta(days=1)
        # using update to bypass validation
        Appointment.objects.filter(pk=appt.pk).update(appointment_date=past_date)
        appt.refresh_from_db()

        success, msg = AdminAppointmentService.cancel_single_appointment(appt.pk)
        assert not success
        assert "Cannot cancel past appointments" in msg
        assert "Cannot cancel past appointments" in msg

    @patch("accounts.notifications.NotificationService.send_notification")
    def test_cancel_single_appointment_success(self, mock_send, setup_data):
        appt = setup_data["appt1"]

        success, msg = AdminAppointmentService.cancel_single_appointment(
            appt.pk, reason="Doctor sick"
        )
        assert success

        appt.refresh_from_db()
        assert appt.status == "CANCELLED"

        # check notification created
        notif = Notification.objects.filter(user=setup_data["patient"].user).first()
        assert notif is not None
        assert "Doctor sick" in notif.message
        mock_send.assert_called_once()

    def test_cancel_single_appointment_not_found(self):
        success, msg = AdminAppointmentService.cancel_single_appointment(9999)
        assert not success
        assert "not found" in msg

    @patch("accounts.models.Notification.objects.create")
    def test_cancel_single_appointment_exception(self, mock_create, setup_data):
        mock_create.side_effect = Exception("DB error")
        success, msg = AdminAppointmentService.cancel_single_appointment(
            setup_data["appt1"].pk
        )
        assert not success
        assert "DB error" in msg

    def test_cancel_doctor_appointments(self, setup_data):
        doc = setup_data["doctor"]
        today = setup_data["today"]

        # Doctor not found
        success, msg, count = AdminAppointmentService.cancel_doctor_appointments(9999)
        assert not success
        assert "Doctor not found" in msg

        # Add another appt
        Appointment.objects.create(
            patient=setup_data["patient"],
            doctor=doc,
            appointment_date=today + timedelta(days=2),
            start_time="10:00:00",
            end_time="10:30:00",
            status="SCHEDULED",
        )

        success, msg, count = AdminAppointmentService.cancel_doctor_appointments(
            doc.pk, reason="Vacation"
        )
        assert success
        assert count == 2

        assert Appointment.objects.filter(status="CANCELLED").count() == 2
        assert Notification.objects.filter(user=setup_data["patient"].user).count() == 2

    def test_cancel_doctor_appointments_specific_date(self, setup_data):
        doc = setup_data["doctor"]
        today = setup_data["today"]

        Appointment.objects.create(
            patient=setup_data["patient"],
            doctor=doc,
            appointment_date=today + timedelta(days=2),
            start_time="10:00:00",
            end_time="10:30:00",
            status="SCHEDULED",
        )

        success, msg, count = AdminAppointmentService.cancel_doctor_appointments(
            doc.pk, date=today + timedelta(days=1)
        )
        assert success
        assert count == 1  # only appt1 cancelled

        setup_data["appt1"].refresh_from_db()
        assert setup_data["appt1"].status == "CANCELLED"

    def test_cancel_doctor_appointments_none_found(self, setup_data):
        setup_data["appt1"].delete()
        success, msg, count = AdminAppointmentService.cancel_doctor_appointments(
            setup_data["doctor"].pk
        )
        assert not success
        assert count == 0
        assert "No active appointments found" in msg

    def test_get_recommendations(self, setup_data):
        doc = setup_data["doctor"]
        patient = setup_data["patient"]
        orig_date = setup_data["today"]

        # Setup doc availability
        DoctorAvailability.objects.create(
            doctor=doc,
            day_of_week=(orig_date + timedelta(days=1)).strftime("%A").upper(),
            start_time="09:00",
            end_time="11:00",
            slot_duration=30,
            is_active=True,
        )

        recs = AdminAppointmentService._get_recommendations(doc, patient, orig_date)
        assert len(recs) > 0
        assert recs[0]["type"] == "same_doctor"
        assert recs[0]["time"] == "09:00 AM"

        # Test alternative doctor
        doc2_user = User.objects.create_user(
            email="doc2@test.com", password="pwd", role="DOCTOR"
        )
        doc2 = Doctor.objects.create(user=doc2_user, specialization="CARDIOLOGY")
        DoctorAvailability.objects.create(
            doctor=doc2,
            day_of_week=(orig_date + timedelta(days=1)).strftime("%A").upper(),
            start_time="14:00",
            end_time="16:00",
            slot_duration=30,
            is_active=True,
        )

        recs2 = AdminAppointmentService._get_recommendations(doc, patient, orig_date)
        # It should contain same doctor and alt doctor
        alt_recs = [r for r in recs2 if r["type"] == "same_specialization"]
        assert len(alt_recs) > 0
        assert alt_recs[0]["doctor_id"] == doc2.pk
