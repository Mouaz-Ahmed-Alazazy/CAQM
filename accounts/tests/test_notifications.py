import pytest
from unittest.mock import patch, MagicMock
from accounts.notifications import NotificationService
from accounts.models import User


@pytest.mark.django_db
class TestNotificationService:
    @patch("accounts.notifications.logger")
    @patch("accounts.notifications.threading.Thread")
    def test_send_notification_success(self, mock_thread, mock_logger):
        user = User.objects.create_user(
            email="test@example.com", first_name="Test", last_name="User"
        )

        result = NotificationService.send_notification(
            user, "REGISTRATION_CONFIRMATION"
        )

        assert result is True
        mock_thread.assert_called_once()
        mock_logger.info.assert_called()

    @patch("accounts.notifications.logger")
    def test_send_notification_invalid_type(self, mock_logger):
        user = User.objects.create_user(email="test@example.com")

        result = NotificationService.send_notification(user, "INVALID_TYPE")

        assert result is False
        mock_logger.error.assert_called_with("Invalid notification type: INVALID_TYPE")

    @patch("accounts.notifications.logger")
    def test_send_notification_missing_context(self, mock_logger):
        user = User.objects.create_user(
            email="test@example.com", first_name="Test", last_name="User"
        )

        # Missing context that BOOKING_CONFIRMATION requires
        result = NotificationService.send_notification(
            user, "BOOKING_CONFIRMATION", context={"date": "2026-03-02"}
        )

        assert result is True
        mock_logger.error.assert_called()  # Key error logged

    @patch("accounts.notifications.NotificationService.send_notification")
    def test_convenience_methods(self, mock_send):
        user = User.objects.create_user(email="test@example.com")
        mock_send.return_value = True

        NotificationService.send_registration_confirmation(user)
        mock_send.assert_called_with(user, "REGISTRATION_CONFIRMATION")

        NotificationService.send_booking_confirmation(
            user, "Dr. Smith", "2026-03-02", "10:00"
        )
        mock_send.assert_called_with(
            user,
            "BOOKING_CONFIRMATION",
            context={"doctor_name": "Dr. Smith", "date": "2026-03-02", "time": "10:00"},
        )

        NotificationService.send_new_appointment_notification(
            user, "Jane Doe", "2026-03-02", "10:00"
        )
        mock_send.assert_called_with(
            user,
            "NEW_APPOINTMENT",
            context={"patient_name": "Jane Doe", "date": "2026-03-02", "time": "10:00"},
        )

    @patch("accounts.notifications.send_mail")
    def test_send_email_async(self, mock_send_mail):
        from django.conf import settings

        expected_from = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@caqm.com")

        NotificationService._send_email_async(
            "Subject", "Message", ["test@example.com"]
        )
        mock_send_mail.assert_called_once_with(
            "Subject",
            "Message",
            expected_from,
            ["test@example.com"],
            fail_silently=False,
        )

    @patch("accounts.notifications.send_mail")
    @patch("accounts.notifications.logger")
    def test_send_email_async_exception(self, mock_logger, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP Error")

        NotificationService._send_email_async(
            "Subject", "Message", ["test@example.com"]
        )
        mock_logger.error.assert_called()
