import requests
import time

BASE_URL = "http://localhost:9000"
NOTIFICATIONS_ENDPOINT = f"{BASE_URL}/api/notifications/"
AUTH_TOKEN = "Bearer your_test_auth_token_here"  # Replace with valid token if needed
HEADERS = {
    "Authorization": AUTH_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json"
}
TIMEOUT = 30

def test_notification_delivery_reliability():
    """
    Test the notification API for reliable delivery with retries on failure
    and multi-channel support including in-app, email, and SMS.
    """
    notification_payload = {
        "recipient_id": 1,  # Assume existing user ID; in a real test, create user and use its ID
        "channels": ["in-app", "email", "sms"],
        "title": "Test Notification Delivery",
        "message": "This is a test notification to verify delivery reliability.",
        "metadata": {
            "appointment_id": 42,
            "priority": "high"
        }
    }
    
    max_retries = 3
    retry_delay_seconds = 2
    response = None

    # Attempt sending notification with retry logic for failure scenarios
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(NOTIFICATIONS_ENDPOINT, json=notification_payload, headers=HEADERS, timeout=TIMEOUT)
            if response.status_code == 200 or response.status_code == 201:
                break  # Success
        except requests.RequestException:
            pass  # Swallow exception and retry

        if attempt < max_retries:
            time.sleep(retry_delay_seconds)
    else:
        assert False, f"Notification sending failed after {max_retries} attempts."

    # Validate response structure and content
    assert response is not None
    assert response.status_code in (200, 201)
    resp_json = response.json()
    assert "notification_id" in resp_json
    notification_id = resp_json["notification_id"]
    assert isinstance(notification_id, int)
    assert resp_json.get("status") in ["sent", "queued", "delivered", "processing"]

    # Verify multi-channel delivery status
    delivery_status = resp_json.get("delivery_status")
    assert delivery_status is not None
    for channel in notification_payload["channels"]:
        assert channel in delivery_status
        # Each channel should have a status indicating success or retry
        channel_status = delivery_status[channel]
        assert channel_status in ["pending", "sent", "failed", "retrying", "delivered"]

    # Optionally, poll the notification status API to confirm final delivery state
    status_url = f"{NOTIFICATIONS_ENDPOINT}{notification_id}/status/"
    final_status = None
    for _ in range(5):
        try:
            status_response = requests.get(status_url, headers=HEADERS, timeout=TIMEOUT)
            if status_response.status_code == 200:
                status_json = status_response.json()
                final_status = status_json.get("final_status")
                if final_status in ["delivered", "failed"]:
                    break
        except requests.RequestException:
            pass
        time.sleep(1)
    assert final_status in ["delivered", "failed"]

test_notification_delivery_reliability()