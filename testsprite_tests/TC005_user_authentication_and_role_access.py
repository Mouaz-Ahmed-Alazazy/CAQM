import requests
import pytest

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

# User credentials and roles to test
USERS = {
    "patient": {"email": "patient@example.com", "password": "PatientPass123", "role": "patient"},
    "doctor": {"email": "doctor@example.com", "password": "DoctorPass123", "role": "doctor"},
    "nurse": {"email": "nurse@example.com", "password": "NursePass123", "role": "nurse"},
    "admin": {"email": "admin@example.com", "password": "AdminPass123", "role": "admin"},
}

# Endpoints for login and a role-protected resource for verification
LOGIN_ENDPOINT = f"{BASE_URL}/api/accounts/login/"
# For access control validation, assume role-specific endpoints
ROLE_ENDPOINTS = {
    "patient": f"{BASE_URL}/api/patients/profile/",
    "doctor": f"{BASE_URL}/api/doctors/schedule/",
    "nurse": f"{BASE_URL}/api/nurses/queue/",
    "admin": f"{BASE_URL}/api/admins/announcements/",
}

def test_user_authentication_and_role_access():
    tokens = {}
    # Login users and obtain tokens
    for role, creds in USERS.items():
        try:
            resp = requests.post(
                LOGIN_ENDPOINT,
                json={"email": creds["email"], "password": creds["password"]},
                timeout=TIMEOUT,
            )
            assert resp.status_code == 200, f"Login failed for {role} with status {resp.status_code}"
            data = resp.json()
            assert "access_token" in data or "token" in data, f"No token returned on login for {role}"
            token = data.get("access_token") or data.get("token")
            tokens[role] = token
        except (requests.RequestException, AssertionError) as e:
            pytest.fail(f"Login request or validation failed for {role}: {e}")

    # Verify access control for each role accessing their allowed resource (should succeed)
    for role, token in tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        try:
            resp = requests.get(ROLE_ENDPOINTS[role], headers=headers, timeout=TIMEOUT)
            assert resp.status_code == 200, f"Access denied for role {role} on own endpoint"
        except (requests.RequestException, AssertionError) as e:
            pytest.fail(f"Access validation failed for role {role}: {e}")

    # Verify roles cannot access endpoints they are not permitted to access (should fail)
    for role, token in tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        forbidden_endpoints = [url for r, url in ROLE_ENDPOINTS.items() if r != role]
        for endpoint in forbidden_endpoints:
            try:
                resp = requests.get(endpoint, headers=headers, timeout=TIMEOUT)
                # Expecting 403 Forbidden or 401 Unauthorized for forbidden access
                assert resp.status_code in (401, 403), (
                    f"Role {role} unexpectedly accessed forbidden endpoint {endpoint} with status {resp.status_code}"
                )
            except requests.RequestException as e:
                pytest.fail(f"Request failed for forbidden access test for role {role} at {endpoint}: {e}")

test_user_authentication_and_role_access()