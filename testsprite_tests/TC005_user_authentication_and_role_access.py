import requests
from requests.exceptions import RequestException

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

# Sample users with different roles for testing login and access
USERS = {
    "patient": {"email": "patient@example.com", "password": "patientpass"},
    "doctor": {"email": "doctor@example.com", "password": "doctorpass"},
    "nurse": {"email": "nurse@example.com", "password": "nursepass"},
    "admin": {"email": "admin@example.com", "password": "adminpass"}
}

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

def test_user_authentication_and_role_access():
    tokens = {}
    try:
        # LOGIN for all user roles
        for role, creds in USERS.items():
            login_url = f"{BASE_URL}/api/accounts/login/"
            payload = {
                "email": creds["email"],
                "password": creds["password"]
            }
            response = requests.post(login_url, json=payload, headers=HEADERS, timeout=TIMEOUT)
            assert response.status_code == 200, f"Login failed for {role} with status {response.status_code}"
            data = response.json()
            assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 0, f"No token returned for {role}"
            tokens[role] = data["token"]

        # ACCESS CONTROL TESTS
        # Mapping roles to their expected accessible endpoints and forbidden endpoints
        access_tests = {
            "patient": {
                "allowed": [
                    f"{BASE_URL}/api/patients/profile/",
                    f"{BASE_URL}/api/appointments/book/",
                ],
                "forbidden": [
                    f"{BASE_URL}/api/admin/users/",
                    f"{BASE_URL}/api/doctors/schedule/",
                ],
            },
            "doctor": {
                "allowed": [
                    f"{BASE_URL}/api/doctors/schedule/",
                    f"{BASE_URL}/api/appointments/my/",
                ],
                "forbidden": [
                    f"{BASE_URL}/api/admin/users/",
                    f"{BASE_URL}/api/patients/profile/",
                ],
            },
            "nurse": {
                "allowed": [
                    f"{BASE_URL}/api/queues/manage/",
                    f"{BASE_URL}/api/appointments/in_progress/",
                ],
                "forbidden": [
                    f"{BASE_URL}/api/admin/users/",
                    f"{BASE_URL}/api/doctors/schedule/",
                ],
            },
            "admin": {
                "allowed": [
                    f"{BASE_URL}/api/admin/users/",
                    f"{BASE_URL}/api/announcements/broadcast/",
                ],
                "forbidden": [
                    f"{BASE_URL}/api/patients/profile/",
                    f"{BASE_URL}/api/appointments/book/",
                ],
            },
        }

        for role, perms in access_tests.items():
            token = tokens[role]
            auth_headers = HEADERS.copy()
            auth_headers["Authorization"] = f"Bearer {token}"

            # Check allowed endpoints
            for url in perms["allowed"]:
                try:
                    resp = requests.get(url, headers=auth_headers, timeout=TIMEOUT)
                    assert resp.status_code in (200, 204), f"{role} should have access to {url} but got {resp.status_code}"
                except RequestException as e:
                    assert False, f"RequestException accessing {url} as {role}: {e}"

            # Check forbidden endpoints
            for url in perms["forbidden"]:
                try:
                    resp = requests.get(url, headers=auth_headers, timeout=TIMEOUT)
                    assert resp.status_code in (401, 403), f"{role} should not have access to {url} but got {resp.status_code}"
                except RequestException as e:
                    assert False, f"RequestException accessing {url} as {role}: {e}"

    except RequestException as err:
        assert False, f"RequestException during test execution: {err}"

# Run the test function
test_user_authentication_and_role_access()
