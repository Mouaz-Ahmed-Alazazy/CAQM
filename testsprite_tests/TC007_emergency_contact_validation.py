import requests
import re

BASE_URL = "http://localhost:9000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}
EMERGENCY_CONTACT_REGEX = r"^(091|092|093|094)\d{7}$"

def test_emergency_contact_validation():
    """
    Test patient registration and update APIs to validate emergency contact field format:
    Must start with 091, 092, 093, or 094 followed by exactly 7 digits.
    """

    patient_create_url = f"{BASE_URL}/accounts/register/"
    patient_detail_url_template = f"{BASE_URL}/patients/{{patient_id}}/"

    def is_valid_emergency_contact(number: str) -> bool:
        return bool(re.match(EMERGENCY_CONTACT_REGEX, number))

    # Prepare valid patient registration data with valid emergency contact
    valid_patient_data = {
        "email": "testuser_emc@example.com",
        "password": "StrongPassw0rd!",
        "first_name": "Test",
        "last_name": "User",
        "emergency_contact": "0911234567",
        "date_of_birth": "1990-01-01"
    }

    # Prepare invalid emergency contacts to test negative cases
    invalid_contacts = [
        "",                      # empty
        "0901234567",            # bad prefix
        "0951234567",            # bad prefix
        "091123456",             # too short
        "09112345678",           # too long
        "09112345a7",            # non-digit character
        "0012345678"             # wrong prefix
    ]

    # 1. Create patient with valid emergency contact - expect success (201 Created)
    patient_id = None
    try:
        resp_create = requests.post(patient_create_url, json=valid_patient_data, headers=HEADERS, timeout=TIMEOUT)
    except Exception as e:
        assert False, f"Exception during patient creation with valid data: {e}"

    assert resp_create.status_code == 201, f"Failed to create patient with valid emergency contact. Status: {resp_create.status_code}, Response: {resp_create.text}"

    patient_created = resp_create.json()
    patient_id = patient_created.get("id")
    assert patient_id, "Created patient response missing 'id'."

    try:
        # Validate the emergency_contact field in response matches regex
        ec = patient_created.get("emergency_contact")
        assert ec is not None, "emergency_contact field missing in create response."
        assert is_valid_emergency_contact(ec), f"Returned emergency_contact '{ec}' is invalid."

        # 2. Attempt to update the patient with each invalid emergency contact - expect failure (400 Bad Request)
        for invalid_contact in invalid_contacts:
            update_payload = {"emergency_contact": invalid_contact}
            try:
                resp_update = requests.put(patient_detail_url_template.format(patient_id=patient_id),
                                           json=update_payload, headers=HEADERS, timeout=TIMEOUT)
            except Exception as e:
                assert False, f"Exception during patient update with invalid emergency_contact '{invalid_contact}': {e}"

            # Expect 400 Bad Request due to validation error
            assert resp_update.status_code == 400, (
                f"Updating emergency_contact with invalid value '{invalid_contact}' did NOT return 400. "
                f"Status: {resp_update.status_code}, Response: {resp_update.text}"
            )

        # 3. Update the patient with another valid emergency contact - expect success
        valid_update_contact = "0947654321"
        update_payload = {"emergency_contact": valid_update_contact}
        resp_update_valid = requests.put(patient_detail_url_template.format(patient_id=patient_id),
                                        json=update_payload, headers=HEADERS, timeout=TIMEOUT)
        assert resp_update_valid.status_code == 200, (
            f"Updating emergency_contact with valid value '{valid_update_contact}' failed. "
            f"Status: {resp_update_valid.status_code}, Response: {resp_update_valid.text}"
        )
        updated_patient = resp_update_valid.json()
        updated_ec = updated_patient.get("emergency_contact")
        assert updated_ec == valid_update_contact, "Emergency contact was not updated correctly."

    finally:
        # Cleanup: delete the created patient
        if patient_id:
            try:
                requests.delete(patient_detail_url_template.format(patient_id=patient_id), headers=HEADERS, timeout=TIMEOUT)
            except Exception:
                pass

test_emergency_contact_validation()
