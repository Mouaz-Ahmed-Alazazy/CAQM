import pytest
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.core.exceptions import ValidationError

from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor
from nurses.models import Nurse
from admins.services import AdminService, AdminDashboardService


@pytest.mark.django_db
class TestAdminService:
    def test_register_user_patient(self):
        with patch(
            "accounts.notifications.NotificationService.send_registration_confirmation"
        ) as mock_send:
            success, user = AdminService.register_user(
                email="new_patient@test.com",
                password="StrongPassword123!",
                first_name="John",
                last_name="Doe",
                phone="1234567890",
                role="PATIENT",
                date_of_birth="1990-01-01",
                address="123 Main St",
                emergency_contact="Jane Doe",
            )
            assert success
            assert user.role == "PATIENT"
            assert user.patient_profile is not None
            assert user.patient_profile.address == "123 Main St"
            mock_send.assert_called_once()

    def test_register_user_doctor(self):
        success, user = AdminService.register_user(
            email="new_doc@test.com",
            password="StrongPassword123!",
            first_name="Doc",
            last_name="Tor",
            phone="1234567890",
            role="DOCTOR",
            specialization="CARDIOLOGY",
        )
        assert success
        assert user.doctor_profile is not None
        assert user.doctor_profile.specialization == "CARDIOLOGY"

    def test_register_user_nurse(self):
        success, user = AdminService.register_user(
            email="new_nurse@test.com",
            password="StrongPassword123!",
            first_name="Nur",
            last_name="Se",
            phone="1234567890",
            role="NURSE",
        )
        assert success
        assert user.nurse_profile is not None

    def test_register_user_invalid_password(self):
        success, msg = AdminService.register_user(
            email="new_user@test.com",
            password="123",  # Invalid
            first_name="Test",
            last_name="Test",
            phone="123",
            role="PATIENT",
        )
        assert not success
        assert "password" in msg.lower()

    @patch("accounts.models.User.objects.create_user")
    def test_register_user_exception(self, mock_create):
        mock_create.side_effect = Exception("DB error")
        success, msg = AdminService.register_user(
            email="new_user@test.com",
            password="StrongPassword123!",
            first_name="Test",
            last_name="Test",
            phone="123",
            role="PATIENT",
        )
        assert not success
        assert "Registration failed" in msg

    def test_get_all_users(self):
        User.objects.create_user(
            email="doc1@test.com", password="pwd", role="DOCTOR", first_name="Alan"
        )
        User.objects.create_user(
            email="pt1@test.com", password="pwd", role="PATIENT", first_name="Bob"
        )

        users = AdminService.get_all_users()
        assert users.count() >= 2

        docs = AdminService.get_all_users(role="DOCTOR")
        assert docs.count() == 1

        search_users = AdminService.get_all_users(search="Alan")
        assert search_users.count() == 1

    @patch("accounts.models.User.objects.all")
    def test_get_all_users_exception(self, mock_all):
        mock_all.side_effect = Exception("DB error")
        users = AdminService.get_all_users()
        assert users.count() == 0

    def test_delete_user(self):
        user = User.objects.create_user(
            email="del@test.com", password="pwd", role="PATIENT"
        )
        success, msg = AdminService.delete_user(user.pk)
        assert success
        assert not User.objects.filter(pk=user.pk).exists()

        success, msg = AdminService.delete_user(9999)
        assert not success
        assert "not found" in msg

    @patch("accounts.models.User.objects.get")
    def test_delete_user_exception(self, mock_get):
        mock_get.side_effect = Exception("DB Error")
        success, msg = AdminService.delete_user(1)
        assert not success
        assert "DB Error" in msg

    def test_update_user_profile(self):
        user = User.objects.create_user(
            email="update@test.com", password="pwd", role="PATIENT"
        )
        Patient.objects.create(user=user)

        success, res = AdminService.update_user_profile(
            user.pk,
            "updated@test.com",
            "John",
            "Doe",
            "999",
            "1990-01-01",
            "MALE",
            address="New Addr",
        )
        assert success
        assert res.email == "updated@test.com"
        assert res.patient_profile.address == "New Addr"

        # Email conflict
        user2 = User.objects.create_user(
            email="conflict@test.com", password="pwd", role="PATIENT"
        )
        success, msg = AdminService.update_user_profile(
            user.pk, "conflict@test.com", "John", "Doe", "999", "1990-01-01", "MALE"
        )
        assert not success
        assert "already exists" in msg

        # Doctor update
        doc_user = User.objects.create_user(
            email="doc_upd@test.com", password="pwd", role="DOCTOR"
        )
        Doctor.objects.create(user=doc_user)
        success, res = AdminService.update_user_profile(
            doc_user.pk,
            "doc_upd@test.com",
            "Dr",
            "John",
            "999",
            "1990-01-01",
            "MALE",
            specialization="DERMATOLOGY",
            profile_photo=None,
        )
        assert success
        assert res.doctor_profile.specialization == "DERMATOLOGY"

        # Nurse update
        nurse_user = User.objects.create_user(
            email="nurse_upd@test.com", password="pwd", role="NURSE"
        )
        Nurse.objects.create(user=nurse_user)
        success, res = AdminService.update_user_profile(
            nurse_user.pk,
            "nurse_upd@test.com",
            "Nu",
            "Rse",
            "999",
            "1990-01-01",
            "FEMALE",
            assigned_doctor=res.doctor_profile,
        )
        assert success
        assert res.nurse_profile.assigned_doctor == doc_user.doctor_profile

        # Not found
        success, msg = AdminService.update_user_profile(
            9999, "a@b.com", "a", "b", "c", "d", "MALE"
        )
        assert not success
        assert "not found" in msg

    @patch("accounts.models.User.objects.get")
    def test_update_user_profile_exception(self, mock_get):
        mock_get.side_effect = Exception("DB Error")
        success, msg = AdminService.update_user_profile(
            1, "a@b.com", "a", "b", "c", "d", "MALE"
        )
        assert not success
        assert "Update failed" in msg
