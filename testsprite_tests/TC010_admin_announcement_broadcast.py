import requests

BASE_URL = "http://localhost:9000"
ADMIN_AUTH_TOKEN = "Bearer admin-token-placeholder"  # Replace with actual admin token before running
TIMEOUT = 30

def test_admin_announcement_broadcast():
    """
    Test the admin announcement API to ensure admins can broadcast important news
    to users and notifications are delivered properly.
    """
    headers = {
        "Authorization": ADMIN_AUTH_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    announcement_payload = {
        "title": "System Maintenance Notification",
        "message": "The clinic system will be down for scheduled maintenance on 2026-01-15 from 01:00 to 05:00.",
        "priority": "high",
        "target_roles": ["patients", "doctors", "nurses", "admins"]
    }

    created_announcement_id = None

    try:
        # Create announcement (POST)
        response = requests.post(
            f"{BASE_URL}/api/admin/announcements/",
            json=announcement_payload,
            headers=headers,
            timeout=TIMEOUT
        )
        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}"
        response_data = response.json()
        assert "id" in response_data, "Response missing announcement id"
        created_announcement_id = response_data["id"]
        assert response_data["title"] == announcement_payload["title"]
        assert response_data["message"] == announcement_payload["message"]
        assert response_data["priority"] == announcement_payload["priority"]
        assert set(response_data.get("target_roles", [])) == set(announcement_payload["target_roles"])

        # Verify announcement retrieval (GET)
        get_response = requests.get(
            f"{BASE_URL}/api/admin/announcements/{created_announcement_id}/",
            headers=headers,
            timeout=TIMEOUT
        )
        assert get_response.status_code == 200, f"Expected 200 OK on get, got {get_response.status_code}"
        get_data = get_response.json()
        assert get_data["id"] == created_announcement_id
        assert get_data["title"] == announcement_payload["title"]

        # Verify notifications delivery status (GET notification delivery status endpoint)
        notifications_response = requests.get(
            f"{BASE_URL}/api/admin/announcements/{created_announcement_id}/notifications-status/",
            headers=headers,
            timeout=TIMEOUT
        )
        assert notifications_response.status_code == 200, (
            f"Expected 200 OK for notifications status, got {notifications_response.status_code}"
        )
        notifications_status = notifications_response.json()
        # Expected keys: delivered, failed, retry_count etc. Validate at least delivered count present
        assert "delivered" in notifications_status, "Notification status missing 'delivered' key"
        # delivered should be integer >= 0
        assert isinstance(notifications_status["delivered"], int) and notifications_status["delivered"] >= 0

    finally:
        # Cleanup: Delete the created announcement if any
        if created_announcement_id:
            del_response = requests.delete(
                f"{BASE_URL}/api/admin/announcements/{created_announcement_id}/",
                headers=headers,
                timeout=TIMEOUT
            )
            # Accept 204 No Content or 200 OK on delete
            assert del_response.status_code in (200, 204), f"Failed to delete announcement with id {created_announcement_id}"

test_admin_announcement_broadcast()