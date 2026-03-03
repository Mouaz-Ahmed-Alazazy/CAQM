import pytest
from accounts.models import User, Notification


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
            date_of_birth="1990-01-01",
            role="PATIENT",
        )
        assert user.email == "testuser@example.com"
        assert user.check_password("testpassword")
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.is_patient() is True
        assert user.is_doctor() is False
        assert user.is_admin() is False
        assert user.is_nurse() is False
        assert str(user) == "Test User (testuser@example.com)"
        assert user.get_full_name() == "Test User"
        assert user.get_short_name() == "Test"

    def test_create_user_no_email(self):
        with pytest.raises(ValueError, match="Users must have an email address"):
            User.objects.create_user(email="", password="testpassword")

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword",
            first_name="Admin",
            last_name="User",
        )
        assert admin.email == "admin@example.com"
        assert admin.is_active is True
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == "ADMIN"
        assert admin.is_admin() is True

    def test_user_roles(self):
        doctor = User.objects.create_user(email="doctor@example.com", role="DOCTOR")
        nurse = User.objects.create_user(email="nurse@example.com", role="NURSE")

        assert doctor.is_doctor() is True
        assert nurse.is_nurse() is True


@pytest.mark.django_db
class TestNotificationModel:
    def test_create_notification(self):
        user = User.objects.create_user(email="test@example.com")
        notification = Notification.objects.create(
            user=user,
            title="Test Title",
            message="Test Message",
            notification_type="GENERAL",
        )

        assert notification.title == "Test Title"
        assert notification.message == "Test Message"
        assert notification.is_read is False
        assert str(notification) == "Test Title - test@example.com"

        assert user.unread_notifications_count() == 1

        notification.is_read = True
        notification.save()

        assert user.unread_notifications_count() == 0
