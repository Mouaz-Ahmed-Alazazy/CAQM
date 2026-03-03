import pytest
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from accounts.models import User
from doctors.models import Doctor
from patients.models import Patient
from appointments.models import Appointment
from queues.models import Queue, PatientQueue
from queues.services import CheckInService


@pytest.mark.django_db
class TestCheckInService:
    @pytest.fixture
    def setup_data(self):
        # Setup users
        doctor_user = User.objects.create_user(
            email="dr@test.com", password="pwd", role="DOCTOR"
        )
        patient_user = User.objects.create_user(
            email="pt@test.com", password="pwd", role="PATIENT"
        )

        doctor = Doctor.objects.create(user=doctor_user)
        patient = Patient.objects.create(user=patient_user)

        today = timezone.localtime().date()

        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            appointment_date=today,
            start_time="10:00:00",
            end_time="10:30:00",
            status="SCHEDULED",
        )

        queue = Queue.objects.create(doctor=doctor, date=today)

        return {
            "doctor_user": doctor_user,
            "patient_user": patient_user,
            "doctor": doctor,
            "patient": patient,
            "today": today,
            "appointment": appointment,
            "queue": queue,
        }

    def test_parse_qr_code_invalid_format(self):
        d, date = CheckInService.parse_qr_code("INVALID-FORMAT")
        assert d is None
        assert date is None

        d, date = CheckInService.parse_qr_code("NOTQUEUE-TOKEN-1-20230101")
        assert d is None
        assert date is None

        d, date = CheckInService.parse_qr_code("QUEUE-TOKEN-abc-20230101")
        assert d is None
        assert date is None

    def test_verify_patient_appointment_not_found(self, setup_data):
        tomorrow = setup_data["today"] + timedelta(days=1)
        appt = CheckInService.verify_patient_appointment(
            setup_data["patient"], setup_data["doctor"], tomorrow
        )
        assert appt is None

    def test_verify_patient_appointment_multiple(self, setup_data):
        # Create without validation to trigger MultipleObjectsReturned
        appt = Appointment(
            doctor=setup_data["doctor"],
            patient=setup_data["patient"],
            appointment_date=setup_data["today"],
            start_time="11:00:00",
            end_time="11:30:00",
            status="SCHEDULED",
        )
        Appointment.objects.bulk_create([appt])

        appt_found = CheckInService.verify_patient_appointment(
            setup_data["patient"], setup_data["doctor"], setup_data["today"]
        )
        assert appt_found is not None
        assert appt_found.start_time.strftime("%H:%M:%S") in ["10:00:00", "11:00:00"]

    def test_verify_doctor_consultation_none(self, setup_data):
        setup_data["appointment"].delete()
        has_appts = CheckInService.verify_doctor_consultation(
            setup_data["doctor"], setup_data["today"]
        )
        assert not has_appts

    def test_is_doctor_checked_in(self, setup_data):
        assert not CheckInService.is_doctor_checked_in(
            setup_data["doctor"], setup_data["today"]
        )
        setup_data["queue"].doctor_check_in_time = timezone.now()
        setup_data["queue"].save()
        assert CheckInService.is_doctor_checked_in(
            setup_data["doctor"], setup_data["today"]
        )

    def test_check_in_patient_already_checked_in(self, setup_data):
        PatientQueue.objects.create(
            queue=setup_data["queue"], patient=setup_data["patient"], status="WAITING"
        )
        success, msg, pq = CheckInService.check_in_patient(
            setup_data["patient"], setup_data["queue"], setup_data["appointment"]
        )
        assert not success
        assert msg == "You are already checked in for this appointment."

    def test_check_in_patient_error(self, setup_data):
        # Trigger an exception by passing None for queue
        success, msg, pq = CheckInService.check_in_patient(
            setup_data["patient"], None, setup_data["appointment"]
        )
        assert not success
        assert "An error occurred" in msg

    def test_check_in_doctor_no_appointments(self, setup_data):
        setup_data["appointment"].delete()
        success, msg, count = CheckInService.check_in_doctor(
            setup_data["doctor"], setup_data["queue"], setup_data["today"]
        )
        assert success
        assert "no scheduled consultations" in msg.lower()

    def test_check_in_doctor_already_checked_in(self, setup_data):
        setup_data["queue"].doctor_check_in_time = timezone.now()
        setup_data["queue"].save()
        success, msg, count = CheckInService.check_in_doctor(
            setup_data["doctor"], setup_data["queue"], setup_data["today"]
        )
        assert not success
        assert "already checked in" in msg

    def test_check_in_doctor_error(self, setup_data):
        with patch(
            "appointments.models.Appointment.objects.filter",
            side_effect=Exception("DB Error"),
        ):
            success, msg, count = CheckInService.check_in_doctor(
                setup_data["doctor"], setup_data["queue"], setup_data["today"]
            )
        assert not success
        assert "An error occurred" in msg

    def test_call_next_patient_no_more(self, setup_data):
        success, msg, pq = CheckInService.call_next_patient(setup_data["queue"].pk)
        assert not success
        assert "No more patients" in msg

    def test_call_next_patient_error(self):
        success, msg, pq = CheckInService.call_next_patient(99999)
        assert not success
        assert "Queue matching query does not exist" in msg

    def test_process_check_in_invalid_format(self, setup_data):
        res = CheckInService.process_check_in(setup_data["doctor_user"], "INVALID")
        assert not res["success"]
        assert "Invalid QR code format" in res["message"]

    def test_process_check_in_wrong_date(self, setup_data):
        tomorrow_str = (setup_data["today"] + timedelta(days=1)).strftime("%Y%m%d")
        qr = f"QUEUE-TOKEN-{setup_data['doctor'].pk}-{tomorrow_str}"
        res = CheckInService.process_check_in(setup_data["doctor_user"], qr)
        assert not res["success"]
        assert "Scan rejected" in res["message"]

    def test_process_check_in_doctor_not_found(self, setup_data):
        qr = f"QUEUE-TOKEN-9999-{setup_data['today'].strftime('%Y%m%d')}"
        res = CheckInService.process_check_in(setup_data["doctor_user"], qr)
        assert not res["success"]
        assert "Doctor not found" in res["message"]

    def test_process_check_in_patient_no_appointment(self, setup_data):
        setup_data["appointment"].delete()
        qr = f"QUEUE-TOKEN-{setup_data['doctor'].pk}-{setup_data['today'].strftime('%Y%m%d')}"
        res = CheckInService.process_check_in(setup_data["patient_user"], qr)
        assert not res["success"]
        assert "no valid appointment found" in res["message"].lower()

    def test_process_check_in_patient_success(self, setup_data):
        qr = f"QUEUE-TOKEN-{setup_data['doctor'].pk}-{setup_data['today'].strftime('%Y%m%d')}"
        res = CheckInService.process_check_in(setup_data["patient_user"], qr)
        assert res["success"]
        assert "Successfully checked in" in res["message"]

    def test_process_check_in_doctor_wrong_doctor(self, setup_data):
        other_doctor = Doctor.objects.create(
            user=User.objects.create_user(
                email="other@test.com", password="pwd", role="DOCTOR"
            )
        )
        qr = f"QUEUE-TOKEN-{other_doctor.pk}-{setup_data['today'].strftime('%Y%m%d')}"
        res = CheckInService.process_check_in(setup_data["doctor_user"], qr)
        assert not res["success"]
        assert "different doctor" in res["message"]

    def test_process_check_in_doctor_no_consultations(self, setup_data):
        setup_data["appointment"].delete()
        qr = f"QUEUE-TOKEN-{setup_data['doctor'].pk}-{setup_data['today'].strftime('%Y%m%d')}"
        res = CheckInService.process_check_in(setup_data["doctor_user"], qr)
        assert res["success"]
        assert "no scheduled consultations" in res["message"].lower()

    def test_process_check_in_invalid_role(self, setup_data):
        admin_user = User.objects.create_superuser(
            email="admin@test.com", password="pwd", role="ADMIN"
        )
        qr = f"QUEUE-TOKEN-{setup_data['doctor'].pk}-{setup_data['today'].strftime('%Y%m%d')}"
        res = CheckInService.process_check_in(admin_user, qr)
        assert not res["success"]
        assert "Invalid user role" in res["message"]
