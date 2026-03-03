import requests
import re

BASE_URL = "http://localhost:9000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}


def test_emergency_contact_validation():
    """
    Test patient registration and profile update APIs to validate emergency contact numbers
    start with 091, 092, 093, or 094 followed by 7 digits.
    """

    def is_valid_emergency_contact(contact):
        pattern = r"^(091|092|093|094)\d{7}$"
        return re.match(pattern, contact) is not None

    # Test data
    valid_emergency_contacts = [
        "0911234567",
        "0927654321",
        "0930000000",
        "0949999999"
    ]

    invalid_emergency_contacts = [
        "0901234567",  # invalid prefix
        "0951234567",  # invalid prefix
        "091123456",   # too short
        "09112345678", # too long
        "091abcdefg",  # letters included
        "0911234!67",  # special character included
        "1234567890",  # no valid prefix
        "",            # empty string
        None           # None type
    ]

    # Patient registration endpoint and patient profile update endpoint
    register_url = f"{BASE_URL}/api/patients/"
    update_url_template = f"{BASE_URL}/api/patients/{{patient_id}}/profile/"

    # Common patient payload base
    patient_payload_base = {
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "password": "StrongPass123!",
        "date_of_birth": "1990-01-01"
    }

    created_patient_id = None

    # Helper to create patient with emergency contact
    def create_patient(emergency_contact):
        payload = patient_payload_base.copy()
        if emergency_contact is not None:
            payload["emergency_contact"] = emergency_contact
        else:
            # Omit emergency_contact field or send null to test validation
            pass
        response = requests.post(register_url, json=payload, headers=HEADERS, timeout=TIMEOUT)
        return response

    # Helper to update patient profile emergency contact (requires patient id)
    def update_patient_emergency_contact(patient_id, emergency_contact):
        payload = {"emergency_contact": emergency_contact}
        url = update_url_template.format(patient_id=patient_id)
        response = requests.put(url, json=payload, headers=HEADERS, timeout=TIMEOUT)
        return response

    # First verify registration with valid emergency contacts succeeds
    for contact in valid_emergency_contacts:
        response = create_patient(contact)
        try:
            assert response.status_code == 201, f"Expected 201 Created for valid contact {contact}, got {response.status_code}"
            # Safely check JSON data
            try:
                data = response.json()
            except Exception:
                data = {}
            assert "id" in data, "Response JSON must contain patient id"
            # Confirm emergency_contact stored matches and format is valid
            stored_contact = data.get("emergency_contact", "")
            assert stored_contact == contact, f"Stored emergency_contact '{stored_contact}' does not match input '{contact}'"
            assert is_valid_emergency_contact(stored_contact), f"Stored emergency_contact '{stored_contact}' is invalid format"
            # Save one created patient for update tests
            if created_patient_id is None:
                created_patient_id = data["id"]
        finally:
            # Cleanup - delete created patient if possible
            try:
                data = response.json()
            except Exception:
                data = {}
            if "id" in data:
                pid = data["id"]
                try:
                    requests.delete(f"{BASE_URL}/api/patients/{pid}/", headers=HEADERS, timeout=TIMEOUT)
                except Exception:
                    pass

    # Check registration fails for invalid emergency contacts
    for contact in invalid_emergency_contacts:
        response = create_patient(contact)
        # Expect 400 Bad Request or validation error response
        # Some APIs might respond 422 or with error code; here accept 400 or 422
        try:
            assert response.status_code in (400, 422), f"Expected 400 or 422 for invalid contact '{contact}', got {response.status_code}"
            # Optionally confirm error message presence
            try:
                data = response.json()
                assert "emergency_contact" in str(data).lower(), "Response should mention emergency_contact validation error"
            except Exception:
                # If response not JSON, ignore
                pass
        finally:
            # If created by mistake, delete
            try:
                data = response.json()
            except Exception:
                data = {}
            if response.status_code == 201 and "id" in data:
                pid = data["id"]
                try:
                    requests.delete(f"{BASE_URL}/api/patients/{pid}/", headers=HEADERS, timeout=TIMEOUT)
                except Exception:
                    pass

    # If no patient was successfully created before, create one for update tests
    if not created_patient_id:
        response = create_patient(valid_emergency_contacts[0])
        assert response.status_code == 201, "Failed to create patient for update tests"
        try:
            data = response.json()
            created_patient_id = data["id"]
        except Exception:
            assert False, "Failed to parse JSON response for created patient"

    # Test profile updates with valid emergency contacts succeed
    for contact in valid_emergency_contacts:
        response = update_patient_emergency_contact(created_patient_id, contact)
        assert response.status_code == 200, f"Expected 200 OK on profile update with valid contact '{contact}', got {response.status_code}"
        try:
            data = response.json()
        except Exception:
            data = {}
        stored_contact = data.get("emergency_contact", "")
        assert stored_contact == contact, f"Updated emergency_contact '{stored_contact}' does not match input '{contact}'"
        assert is_valid_emergency_contact(stored_contact), f"Updated emergency_contact '{stored_contact}' is invalid format"

    # Test profile updates with invalid contacts fail
    for contact in invalid_emergency_contacts:
        response = update_patient_emergency_contact(created_patient_id, contact)
        assert response.status_code in (400, 422), f"Expected validation failure status for invalid update contact '{contact}', got {response.status_code}"
        # Optionally check error message in response
        try:
            data = response.json()
            assert "emergency_contact" in str(data).lower(), "Response should mention emergency_contact validation error"
        except Exception:
            pass

    # Cleanup created patient after update tests
    if created_patient_id:
        try:
            requests.delete(f"{BASE_URL}/api/patients/{created_patient_id}/", headers=HEADERS, timeout=TIMEOUT)
        except Exception:
            pass


test_emergency_contact_validation()
