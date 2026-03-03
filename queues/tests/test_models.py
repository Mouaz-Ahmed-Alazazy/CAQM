import pytest
from django.utils import timezone
from datetime import timedelta
import os
import json
from unittest.mock import patch, mock_open

from accounts.models import User
from doctors.models import Doctor, DoctorAvailability
from patients.models import Patient
from queues.models import Queue, PatientQueue
from django.conf import settings


@pytest.mark.django_db
class TestQueueModel:
    @pytest.fixture
    def setup_data(self):
        doctor_user = User.objects.create_user(
            email="dr_queue@test.com", password="pwd", role="DOCTOR"
        )
        doctor = Doctor.objects.create(user=doctor_user)
        patient_user = User.objects.create_user(
            email="pt_queue@test.com", password="pwd", role="PATIENT"
        )
        patient = Patient.objects.create(user=patient_user)

        queue = Queue.objects.create(doctor=doctor, date=timezone.localtime().date())

        return {"doctor": doctor, "patient": patient, "queue": queue}

    def test_queue_str(self, setup_data):
        q = setup_data["queue"]
        assert str(q) == f"Queue for {q.doctor} on {q.date}"

    def test_queue_is_empty(self, setup_data):
        q = setup_data["queue"]
        assert q.is_empty()
        PatientQueue.objects.create(queue=q, patient=setup_data["patient"], position=1)
        assert not q.is_empty()

    def test_queue_enqueue_dequeue(self, setup_data):
        q = setup_data["queue"]
        # Enqueue with object
        pq1 = q.enqueue(setup_data["patient"])
        assert pq1.patient == setup_data["patient"]

        # Enqueue with ID
        patient2 = Patient.objects.create(
            user=User.objects.create_user(
                email="pt2@test.com", password="pwd", role="PATIENT"
            )
        )
        pq2 = q.enqueue(patient2.pk)
        assert pq2.patient == patient2

        # Dequeue
        next_p = q.dequeue()
        assert next_p == pq1
        assert next_p.status == "IN_PROGRESS"

        next_p2 = q.dequeue()
        assert next_p2 == pq2

        assert q.dequeue() is None

    def test_queue_validate_qrcode(self, setup_data):
        q = setup_data["queue"]
        assert q.validate_qrcode(q.qrcode)
        assert not q.validate_qrcode("wrong_code")

    def test_queue_get_qrcode_image(self, setup_data):
        q = setup_data["queue"]
        assert q.get_qrcode_image() != ""

        q.qrcode_image = None
        assert q.get_qrcode_image() == ""

    @patch("os.path.exists", return_value=True)
    def test_generate_qrcode_json_error_handled(self, mock_exists, setup_data):
        # Trigger an exception during json load/dump to ensure it's handled
        with patch("builtins.open", mock_open(read_data="invalid json")):
            q = Queue(
                doctor=setup_data["doctor"],
                date=timezone.localtime().date() + timedelta(days=1),
            )
            q.generate_qrcode()  # Shouldn't raise error
            assert q.qrcode is not None

    def test_get_estimated_wait_time(self, setup_data):
        q = setup_data["queue"]

        # Default duration is 20 if no availability
        assert q.get_estimated_wait_time(1) == 0
        assert q.get_estimated_wait_time(2) == 20
        assert q.get_estimated_wait_time(3) == 40

        # Create availability
        DoctorAvailability.objects.create(
            doctor=setup_data["doctor"],
            day_of_week=q.date.strftime("%A").upper(),
            start_time="09:00",
            end_time="17:00",
            slot_duration=15,
            is_active=True,
        )
        assert q.get_estimated_wait_time(2) == 15

        now_time = timezone.now()
        with patch("django.utils.timezone.now", return_value=now_time):
            # Add active consultation
            pq = PatientQueue.objects.create(
                queue=q, patient=setup_data["patient"], position=1, status="IN_PROGRESS"
            )
            pq.consultation_start_time = now_time - timedelta(minutes=5)
            pq.save()

            # 15 min slot - 5 elapsed = 10 remaining
            wait_time = q.get_estimated_wait_time(2)
            assert wait_time == 25  # 15 for person ahead + 10 remaining

            # Elapsed more than slot duration
            pq.consultation_start_time = now_time - timedelta(minutes=20)
            pq.save()
            assert q.get_estimated_wait_time(2) == 15  # Remaining becomes 0

    def test_get_size(self, setup_data):
        q = setup_data["queue"]
        assert q.get_size() == 0
        PatientQueue.objects.create(queue=q, patient=setup_data["patient"], position=1)
        assert q.get_size() == 1


@pytest.mark.django_db
class TestPatientQueueModel:
    @pytest.fixture
    def setup_data(self):
        doctor = Doctor.objects.create(
            user=User.objects.create_user(
                email="dr2@test.com", password="pwd", role="DOCTOR"
            )
        )
        patient1 = Patient.objects.create(
            user=User.objects.create_user(
                email="pt1@test.com", password="pwd", role="PATIENT"
            )
        )
        patient2 = Patient.objects.create(
            user=User.objects.create_user(
                email="pt2@test.com", password="pwd", role="PATIENT"
            )
        )
        patient3 = Patient.objects.create(
            user=User.objects.create_user(
                email="pt3@test.com", password="pwd", role="PATIENT"
            )
        )

        queue = Queue.objects.create(doctor=doctor, date=timezone.localtime().date())
        pq1 = PatientQueue.objects.create(queue=queue, patient=patient1)
        pq2 = PatientQueue.objects.create(queue=queue, patient=patient2)
        pq3 = PatientQueue.objects.create(queue=queue, patient=patient3)

        return {"queue": queue, "pq1": pq1, "pq2": pq2, "pq3": pq3}

    def test_str(self, setup_data):
        pq = setup_data["pq1"]
        assert str(pq) == f"{pq.patient} in {pq.queue} at position {pq.position}"

    def test_update_status(self, setup_data):
        pq = setup_data["pq1"]
        assert pq.status == "WAITING"

        pq.update_status()
        assert pq.status == "IN_PROGRESS"

        pq.update_status()
        assert pq.status == "TERMINATED"

        pq.update_status("NO_SHOW")
        assert pq.status == "NO_SHOW"

    def test_get_wait_time(self, setup_data):
        pq = setup_data["pq1"]
        # By default check_in_time is set
        assert pq.get_wait_time() >= 0
        assert isinstance(pq.get_wait_time_display(), str)

        pq.check_in_time = None
        assert pq.get_wait_time() == 0

    def test_format_minutes(self):
        assert PatientQueue.format_minutes(0) == "Soon"
        assert PatientQueue.format_minutes(-5) == "Soon"
        assert PatientQueue.format_minutes(45) == "45 min"
        assert PatientQueue.format_minutes(60) == "1 hr"
        assert PatientQueue.format_minutes(75) == "1 hr 15 min"
        assert PatientQueue.format_minutes(120) == "2 hrs"
        assert PatientQueue.format_minutes(130) == "2 hrs 10 min"

    def test_get_consultation_duration(self, setup_data):
        pq = setup_data["pq1"]
        assert pq.get_consultation_duration() == 0

        pq.consultation_start_time = timezone.now() - timedelta(minutes=30)
        pq.consultation_end_time = timezone.now()
        assert pq.get_consultation_duration() == 30
        assert pq.get_consultation_duration_display() == "30 min"

    def test_get_estimated_time_display(self, setup_data):
        pq = setup_data["pq1"]
        pq.estimated_time = 45
        assert pq.get_estimated_time_display() == "45 min"

    def test_mark_as_emergency(self, setup_data):
        pq3 = setup_data["pq3"]
        pq1 = setup_data["pq1"]
        pq2 = setup_data["pq2"]

        pq3.mark_as_emergency()

        pq3.refresh_from_db()
        pq1.refresh_from_db()
        pq2.refresh_from_db()

        assert pq3.position == 1
        assert pq3.is_emergency is True
        assert pq3.status == "EMERGENCY"
        assert pq1.position == 2
        assert pq2.position == 3

    def test_update_position_move_up(self, setup_data):
        pq1, pq2, pq3 = setup_data["pq1"], setup_data["pq2"], setup_data["pq3"]

        # move 3 to 1
        pq3.update_position(1)

        pq1.refresh_from_db()
        pq2.refresh_from_db()
        pq3.refresh_from_db()

        assert pq3.position == 1
        assert pq1.position == 2
        assert pq2.position == 3

    def test_update_position_move_down(self, setup_data):
        pq1, pq2, pq3 = setup_data["pq1"], setup_data["pq2"], setup_data["pq3"]

        # move 1 to 2
        pq1.update_position(2)

        pq1.refresh_from_db()
        pq2.refresh_from_db()
        pq3.refresh_from_db()

        assert pq1.position == 2
        assert pq2.position == 1
        assert pq3.position == 3
