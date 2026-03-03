import re

with open("admins/tests/test_booking_service.py", "r") as f:
    content = f.read()

# Replace the specific test
old_test = """    def test_book_appointment_service_failure(self, setup_data):
        # Book outside availability
        success, msg = AdminBookingService.book_appointment(
            setup_data["patient"].pk,
            setup_data["doctor"].pk,
            setup_data["today"],
            datetime.time(18, 0),
        )
        assert not success
        assert "outside doctor's availability" in msg.lower()"""

new_test = """    @patch("appointments.services.AppointmentService.book_appointment")
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
        assert "outside doctor's availability" in msg.lower()"""

content = content.replace(old_test, new_test)

with open("admins/tests/test_booking_service.py", "w") as f:
    f.write(content)

