import requests

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

# Admin credentials for authentication - adjust as needed
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "adminpassword"

def get_admin_token():
    """
    Authenticate as admin to get a JWT token.
    Adjusted endpoint to '/api/token/' from '/api/auth/login/' and token extraction accordingly.
    """
    login_url = f"{BASE_URL}/api/token/"
    payload = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    try:
        resp = requests.post(login_url, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Failed to authenticate admin user: {e}"
    data = resp.json()
    token = data.get("access")
    if not token:
        assert False, "Authentication did not return an access token"
    return token

def create_announcement(token, title, message):
    url = f"{BASE_URL}/api/admin/announcements/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": title,
        "message": message,
        "broadcast": True  # Assuming a broadcast flag to trigger notifications
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Announcement creation request failed: {e}"
    return response.json()

def delete_announcement(token, announcement_id):
    url = f"{BASE_URL}/api/admin/announcements/{announcement_id}/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        resp = requests.delete(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        # Log but do not fail test on cleanup failure
        print(f"Warning: Failed to delete announcement {announcement_id}: {e}")

def get_notifications(token, announcement_title):
    url = f"{BASE_URL}/api/notifications/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Fetching notifications failed: {e}"
    notifications = resp.json()
    # Filter notifications related to the announcement title
    filtered = [n for n in notifications if announcement_title in n.get("message", "") or announcement_title in n.get("title", "")]
    return filtered

def test_admin_announcement_broadcast():
    token = get_admin_token()
    announcement_title = "Important Clinic Update"
    announcement_message = "All patients must wear masks starting next week."
    announcement = None

    try:
        # Create announcement
        announcement = create_announcement(token, announcement_title, announcement_message)
        announcement_id = announcement.get("id")
        assert announcement_id is not None, "Announcement ID missing in response"
        assert announcement.get("title") == announcement_title
        assert announcement.get("message") == announcement_message
        assert announcement.get("broadcast") is True or announcement.get("status") == "broadcasted"

        # Validate that notification for announcement is delivered properly
        # This may require some delay or retry mechanism if notifications are processed asynchronously
        import time
        retries = 5
        found_notifications = []
        for _ in range(retries):
            found_notifications = get_notifications(token, announcement_title)
            if found_notifications:
                break
            time.sleep(2)
        assert found_notifications, "No notification related to announcement found"

        # Check notification content correctness
        for notif in found_notifications:
            assert "title" in notif or "message" in notif
            # Notification should mention the announcement message or title
            assert announcement_title in notif.get("title", "") or announcement_message in notif.get("message", "")

    finally:
        if announcement and announcement.get("id"):
            delete_announcement(token, announcement["id"])

test_admin_announcement_broadcast()
