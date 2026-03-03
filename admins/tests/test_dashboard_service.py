import pytest
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor
from nurses.models import Nurse
from appointments.models import Appointment
from queues.models import Queue, PatientQueue
from admins.services import AdminDashboardService


@pytest.mark.django_db
class TestAdminDashboardService:
    @pytest.fixture
    def setup_data(self):
        doctor = Doctor.objects.create(
            user=User.objects.create_user(
                email="doc@test.com", password="pwd", role="DOCTOR"
            )
        )
        patient = Patient.objects.create(
            user=User.objects.create_user(
                email="pt@test.com", password="pwd", role="PATIENT"
            )
        )
        nurse = Nurse.objects.create(
            user=User.objects.create_user(
                email="nurse@test.com", password="pwd", role="NURSE"
            )
        )
        admin = User.objects.create_superuser(
            email="admin@test.com", password="pwd", role="ADMIN"
        )

        today = timezone.localtime().date()
        queue = Queue.objects.create(doctor=doctor, date=today)
        pq = PatientQueue.objects.create(queue=queue, patient=patient, status="WAITING")

        appt = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=today,
            start_time="10:00:00",
            end_time="10:30:00",
            status="SCHEDULED",
        )

        return {
            "doctor": doctor,
            "patient": patient,
            "nurse": nurse,
            "admin": admin,
            "queue": queue,
            "pq": pq,
            "appt": appt,
            "today": today,
        }

    def test_get_overview_stats(self, setup_data):
        now_date = setup_data["today"]
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value.date.return_value = now_date
            stats = AdminDashboardService.get_overview_stats()
            assert stats["total_doctors"] == 1
            assert stats["total_patients"] == 1
            assert stats["total_nurses"] == 1
            assert stats["total_admins"] == 1
            assert stats["today_appointments"] == 1
            assert stats["active_queues"] == 1
            assert stats["total_users"] == 4

    def test_get_doctor_queue_stats(self, setup_data):
        doc = setup_data["doctor"]
        now_date = setup_data["today"]
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value.date.return_value = now_date
            stats = AdminDashboardService.get_doctor_queue_stats(doctor_id=doc.pk)

            assert len(stats) == 1
            assert stats[0]["doctor_id"] == doc.pk

            all_stats = AdminDashboardService.get_doctor_queue_stats()
            assert len(all_stats) == 1

    def test_get_past_stats(self, setup_data):
        doc = setup_data["doctor"]
        yesterday = setup_data["today"] - timedelta(days=1)

        past_q = Queue.objects.create(doctor=doc, date=yesterday)
        past_pq = PatientQueue.objects.create(
            queue=past_q, patient=setup_data["patient"], status="TERMINATED"
        )
        past_pq.consultation_start_time = timezone.now() - timedelta(hours=25)
        past_pq.consultation_end_time = past_pq.consultation_start_time + timedelta(
            minutes=10
        )
        past_pq.save()

        PatientQueue.objects.filter(pk=past_pq.pk).update(estimated_time=15)

        stats = AdminDashboardService._get_past_stats(
            doc, setup_data["today"] - timedelta(days=7), setup_data["today"]
        )
        assert stats["total_booked"] == 1
        assert stats["completed"] == 1
        assert stats["completion_rate"] == 100.0
        assert stats["avg_duration_minutes"] == 10
        assert stats["avg_estimated_minutes"] == 15

    def test_get_today_stats_no_queue(self, setup_data):
        setup_data["queue"].delete()
        stats = AdminDashboardService._get_today_stats(
            setup_data["doctor"], setup_data["today"]
        )
        assert not stats["has_queue"]
        assert stats["total_booked"] == 1

    def test_get_today_stats_with_queue(self, setup_data):
        stats = AdminDashboardService._get_today_stats(
            setup_data["doctor"], setup_data["today"]
        )
        assert stats["has_queue"]
        assert stats["total_booked"] == 1
        assert stats["waiting"] == 1

    def test_get_future_stats(self, setup_data):
        doc = setup_data["doctor"]
        tomorrow = setup_data["today"] + timedelta(days=1)

        Appointment.objects.create(
            patient=setup_data["patient"],
            doctor=doc,
            appointment_date=tomorrow,
            start_time="10:00:00",
            end_time="10:30:00",
            status="SCHEDULED",
            notes="Urgent case",
        )

        stats = AdminDashboardService._get_future_stats(
            doc, setup_data["today"], tomorrow + timedelta(days=1)
        )
        assert stats["scheduled_appointments"] == 1
        assert stats["urgent"] == 1

    def test_get_today_summary(self, setup_data):
        now_date = setup_data["today"]
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value.date.return_value = now_date
            summary = AdminDashboardService.get_today_summary()
            assert summary["scheduled_appointments"] == 1
            assert summary["waiting"] == 1

    def test_get_recent_activity(self, setup_data):
        pq = setup_data["pq"]
        pq.status = "TERMINATED"
        pq.patient.user.first_name = "Alan"
        pq.patient.user.save()
        pq.save()

        activity = AdminDashboardService.get_recent_activity()
        assert activity.count() == 1
        assert activity.first().status == "TERMINATED"

        assert AdminDashboardService.get_recent_activity(status="WAITING").count() == 0
        assert AdminDashboardService.get_recent_activity(search="Alan").count() == 1
        assert (
            AdminDashboardService.get_recent_activity(
                date_from=setup_data["today"], date_to=setup_data["today"]
            ).count()
            == 1
        )
