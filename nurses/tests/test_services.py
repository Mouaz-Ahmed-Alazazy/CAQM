import pytest
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from accounts.models import User
from doctors.models import Doctor
from patients.models import Patient
from appointments.models import Appointment
from queues.models import Queue, PatientQueue
from nurses.models import Nurse
from nurses.services import NurseService
from queues.services import CheckInService


@pytest.mark.django_db
class TestNurseService:
    @pytest.fixture
    def setup_data(self):
        doctor_user = User.objects.create_user(
            email="dr_nurse@test.com", password="pwd", role="DOCTOR"
        )
        doctor = Doctor.objects.create(user=doctor_user)

        nurse_user = User.objects.create_user(
            email="nurse@test.com", password="pwd", role="NURSE"
        )
        nurse = Nurse.objects.create(user=nurse_user, assigned_doctor=doctor)

        patient_user1 = User.objects.create_user(
            email="pt1@test.com", password="pwd", role="PATIENT"
        )
        patient1 = Patient.objects.create(user=patient_user1)

        patient_user2 = User.objects.create_user(
            email="pt2@test.com", password="pwd", role="PATIENT"
        )
        patient2 = Patient.objects.create(user=patient_user2)

        today = timezone.now().date()
        queue = Queue.objects.create(doctor=doctor, date=today)

        appt = Appointment.objects.create(
            patient=patient1,
            doctor=doctor,
            appointment_date=today,
            start_time="10:00:00",
            end_time="10:30:00",
            status="CHECKED_IN",
        )

        return {
            "doctor": doctor,
            "nurse": nurse,
            "patient1": patient1,
            "patient2": patient2,
            "queue": queue,
            "today": today,
            "appointment": appt,
        }

    def test_get_assigned_doctor_queue(self, setup_data):
        nurse = setup_data["nurse"]

        queue = NurseService.get_assigned_doctor_queue(nurse)
        assert queue == setup_data["queue"]

        nurse.assigned_doctor = None
        nurse.save()
        assert NurseService.get_assigned_doctor_queue(nurse) is None

    def test_get_queue_patients(self, setup_data):
        q = setup_data["queue"]
        assert NurseService.get_queue_patients(None).count() == 0

        PatientQueue.objects.create(queue=q, patient=setup_data["patient1"], position=1)
        PatientQueue.objects.create(queue=q, patient=setup_data["patient2"], position=2)

        pts = NurseService.get_queue_patients(q)
        assert pts.count() == 2
        assert pts[0].patient == setup_data["patient1"]

    def test_get_waiting_patients(self, setup_data):
        q = setup_data["queue"]
        assert NurseService.get_waiting_patients(None).count() == 0

        PatientQueue.objects.create(
            queue=q, patient=setup_data["patient1"], position=1, status="IN_PROGRESS"
        )
        PatientQueue.objects.create(
            queue=q, patient=setup_data["patient2"], position=2, status="WAITING"
        )

        pts = NurseService.get_waiting_patients(q)
        assert pts.count() == 1
        assert pts[0].patient == setup_data["patient2"]

    def test_get_current_patient(self, setup_data):
        q = setup_data["queue"]
        assert NurseService.get_current_patient(None) is None
        assert NurseService.get_current_patient(q) is None

        pq = PatientQueue.objects.create(
            queue=q, patient=setup_data["patient1"], position=1, status="IN_PROGRESS"
        )
        assert NurseService.get_current_patient(q) == pq

    def test_call_next_patient(self, setup_data):
        q = setup_data["queue"]
        # No queue
        success, msg = NurseService.call_next_patient(None)
        assert not success
        assert "No queue" in msg

        # Doctor not checked in
        success, msg = NurseService.call_next_patient(q)
        assert not success
        assert "Doctor hasn't checked in" in msg

        # Doctor checked in
        q.doctor_check_in_time = timezone.now()
        q.save()

        # No patients waiting
        success, msg = NurseService.call_next_patient(q)
        assert not success
        assert "No patients waiting" in msg

        # Add waiting patient
        pq1 = PatientQueue.objects.create(
            queue=q, patient=setup_data["patient1"], position=1, status="WAITING"
        )
        success, next_pt = NurseService.call_next_patient(q)
        assert success
        assert next_pt == pq1
        assert next_pt.status == "IN_PROGRESS"

        # Already in progress
        success, msg = NurseService.call_next_patient(q)
        assert not success
        assert "Please complete consultation with" in msg

    def test_start_consultation(self, setup_data):
        q = setup_data["queue"]
        pq = PatientQueue.objects.create(
            queue=q, patient=setup_data["patient1"], position=1, status="WAITING"
        )

        # Exception / Not found
        success, msg = NurseService.start_consultation(9999)
        assert not success
        assert "not found" in msg

        # Doctor not checked in
        success, msg = NurseService.start_consultation(pq.pk)
        assert not success
        assert "Doctor hasn't checked in" in msg

        q.doctor_check_in_time = timezone.now()
        q.save()

        # Success
        success, result = NurseService.start_consultation(pq.pk)
        assert success
        assert result.status == "IN_PROGRESS"

        # Appt status should be updated
        setup_data["appointment"].refresh_from_db()
        assert setup_data["appointment"].status == "IN_PROGRESS"

        # Already in progress prevents another from starting
        pq2 = PatientQueue.objects.create(
            queue=q, patient=setup_data["patient2"], position=2, status="WAITING"
        )
        success, msg = NurseService.start_consultation(pq2.pk)
        assert not success
        assert "complete consultation with" in msg

        # Try to start not waiting patient
        pq2.status = "TERMINATED"
        pq2.save()
        success, msg = NurseService.start_consultation(pq2.pk)
        assert not success
        assert "not in waiting status" in msg

    @patch("nurses.services.PatientQueue.objects.get")
    def test_start_consultation_exception(self, mock_get, setup_data):
        mock_get.side_effect = Exception("DB Error")
        success, msg = NurseService.start_consultation(1)
        assert not success
        assert "DB Error" in msg

    def test_end_consultation(self, setup_data):
        q = setup_data["queue"]
        pq = PatientQueue.objects.create(
            queue=q, patient=setup_data["patient1"], position=1, status="IN_PROGRESS"
        )
        setup_data["appointment"].status = "IN_PROGRESS"
        setup_data["appointment"].save()

        # Not found
        success, msg = NurseService.end_consultation(9999)
        assert not success

        # Not in progress
        pq.status = "WAITING"
        pq.save()
        success, msg = NurseService.end_consultation(pq.pk)
        assert not success
        assert "not in consultation" in msg

        # Success
        pq.status = "IN_PROGRESS"
        pq.save()
        success, result = NurseService.end_consultation(pq.pk)
        assert success
        assert result.status == "TERMINATED"
        assert result.consultation_end_time is not None

        setup_data["appointment"].refresh_from_db()
        assert setup_data["appointment"].status == "COMPLETED"

    @patch("nurses.services.PatientQueue.objects.get")
    def test_end_consultation_exception(self, mock_get, setup_data):
        mock_get.side_effect = Exception("DB Error")
        success, msg = NurseService.end_consultation(1)
        assert not success
        assert "DB Error" in msg

    def test_mark_no_show(self, setup_data):
        q = setup_data["queue"]
        pq = PatientQueue.objects.create(
            queue=q, patient=setup_data["patient1"], position=1, status="WAITING"
        )
        pq.consultation_start_time = timezone.now()
        pq.save()

        # Not found
        success, msg = NurseService.mark_no_show(9999)
        assert not success

        # Invalid status
        pq.status = "TERMINATED"
        pq.save()
        success, msg = NurseService.mark_no_show(pq.pk)
        assert not success
        assert "Can only mark waiting or in-progress" in msg

        # Success
        pq.status = "WAITING"
        pq.save()
        success, result = NurseService.mark_no_show(pq.pk)
        assert success
        assert result.status == "NO_SHOW"
        assert result.consultation_start_time is None

        setup_data["appointment"].refresh_from_db()
        assert setup_data["appointment"].status == "NO_SHOW"

    @patch("nurses.services.PatientQueue.objects.get")
    def test_mark_no_show_exception(self, mock_get, setup_data):
        mock_get.side_effect = Exception("DB Error")
        success, msg = NurseService.mark_no_show(1)
        assert not success
        assert "DB Error" in msg

    def test_get_queue_statistics(self, setup_data):
        assert NurseService.get_queue_statistics(None)["total"] == 0

        q = setup_data["queue"]
        PatientQueue.objects.create(
            queue=q, patient=setup_data["patient1"], status="WAITING"
        )
        PatientQueue.objects.create(
            queue=q, patient=setup_data["patient2"], status="IN_PROGRESS"
        )

        patient3 = Patient.objects.create(
            user=User.objects.create_user(
                email="pt3@test.com", password="pwd", role="PATIENT"
            )
        )
        PatientQueue.objects.create(queue=q, patient=patient3, status="TERMINATED")

        patient4 = Patient.objects.create(
            user=User.objects.create_user(
                email="pt4@test.com", password="pwd", role="PATIENT"
            )
        )
        PatientQueue.objects.create(queue=q, patient=patient4, status="NO_SHOW")

        stats = NurseService.get_queue_statistics(q)
        assert stats["total"] == 4
        assert stats["waiting"] == 1
        assert stats["in_progress"] == 1
        assert stats["completed"] == 1
        assert stats["no_show"] == 1
