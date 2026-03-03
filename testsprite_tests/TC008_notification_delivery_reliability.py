import requests
import time

BASE_URL = "http://localhost:9000"
NOTIFICATIONS_ENDPOINT = f"{BASE_URL}/api/notifications/"
HEADERS = {"Content-Type": "application/json"}

def test_notification_delivery_reliability():
    """
    Test the notification API to ensure:
    - Reliable delivery with retries on failure
    - Support for multi-channel delivery: in-app, email, SMS
    """

    notification_payload = {
        "recipient_id": None,  # Will set after patient creation
        "channels": ["in_app", "email", "sms"],
        "title": "Test Notification Delivery Reliability",
        "message": "This is a test notification sent to multiple channels to verify reliable delivery with retries.",
        "priority": "high"
    }

    # Helper function to create a patient user for notification recipient
    def create_test_patient():
        url = f"{BASE_URL}/api/patients/"
        patient_data = {
            "first_name": "Test",
            "last_name": "NotificationRecipient",
            "email": "test.notificationrecipient@example.com",
            "emergency_contact": "0911234567"
        }
        response = requests.post(url, json=patient_data, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()["id"]

    # Helper function to delete a patient user after test
    def delete_test_patient(patient_id):
        url = f"{BASE_URL}/api/patients/{patient_id}/"
        try:
            requests.delete(url, headers=HEADERS, timeout=30)
        except Exception:
            pass

    # Helper function to send notification with retries on failure
    def send_notification_with_retries(payload, max_retries=3, delay=2):
        attempt = 0
        last_response = None
        while attempt < max_retries:
            try:
                resp = requests.post(NOTIFICATIONS_ENDPOINT, json=payload, headers=HEADERS, timeout=30)
                if resp.status_code == 200 or resp.status_code == 201:
                    return resp
                else:
                    last_response = resp
            except requests.RequestException as e:
                last_response = e
            attempt += 1
            time.sleep(delay)
        return last_response

    # Main test logic
    patient_id = None
    try:
        # Create a test patient to receive notification
        patient_id = create_test_patient()
        notification_payload["recipient_id"] = patient_id

        # Send notification with retries
        response = send_notification_with_retries(notification_payload)

        # Assert final response is success
        assert response is not None, "No response received from notification API"
        if isinstance(response, requests.Response):
            assert response.status_code in [200, 201], f"Notification API failed with status {response.status_code}"
            resp_json = response.json()
            # Validate that all requested channels are in response
            assert "delivered_channels" in resp_json, "Response missing 'delivered_channels' field"
            delivered_channels = resp_json["delivered_channels"]
            # Check all requested channels reported as delivered or at least attempted
            for ch in notification_payload["channels"]:
                assert ch in delivered_channels, f"Channel '{ch}' not in delivered channels: {delivered_channels}"
            # Validate retry count if present
            if "retry_count" in resp_json:
                assert resp_json["retry_count"] <= 3, "Retry count exceeded max retries"
        else:
            # last_response was an exception
            assert False, f"Notification API request failed with exception: {response}"

    finally:
        if patient_id:
            delete_test_patient(patient_id)

test_notification_delivery_reliability()