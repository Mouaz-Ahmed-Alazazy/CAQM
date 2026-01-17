import requests
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:9000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}

def create_doctor():
    payload = {
        "name": "Dr. Test",
        "specialization": "General",
        "email": f"drtest{uuid.uuid4().hex[:8]}@clinic.test"
    }
    response = requests.post(f"{BASE_URL}/api/doctors/", json=payload, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()

def delete_doctor(doctor_id):
    requests.delete(f"{BASE_URL}/api/doctors/{doctor_id}/", timeout=TIMEOUT)

def create_patient():
    payload = {
        "name": "Patient Test",
        "email": f"patienttest{uuid.uuid4().hex[:8]}@clinic.test",
        "emergency_contact": "0911234567"
    }
    response = requests.post(f"{BASE_URL}/api/patients/", json=payload, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()

def delete_patient(patient_id):
    requests.delete(f"{BASE_URL}/api/patients/{patient_id}/", timeout=TIMEOUT)

def create_appointment(patient_id, doctor_id, appointment_date, start_time, status="SCHEDULED"):
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "start_time": start_time,
        "status": status,
        "type": "scheduled"
    }
    response = requests.post(f"{BASE_URL}/api/appointments/", json=payload, headers=HEADERS, timeout=TIMEOUT)
    return response

def modify_appointment_status(appointment_id, new_status):
    payload = {"status": new_status}
    response = requests.patch(f"{BASE_URL}/api/appointments/{appointment_id}/", json=payload, headers=HEADERS, timeout=TIMEOUT)
    return response

def cancel_appointment(appointment_id):
    payload = {"status": "CANCELLED"}
    response = requests.patch(f"{BASE_URL}/api/appointments/{appointment_id}/", json=payload, headers=HEADERS, timeout=TIMEOUT)
    return response

def test_appointment_modification_and_cancellation():
    doctor = patient = appointment = None
    try:
        # Create doctor and patient resources
        doctor = create_doctor()
        patient = create_patient()

        # Appointment date/time - a date in the future with valid time
        appointment_date = (datetime.now() + timedelta(days=3)).date().isoformat()
        start_time = "10:00"

        # Create a scheduled appointment
        create_resp = create_appointment(patient["id"], doctor["id"], appointment_date, start_time)
        assert create_resp.status_code == 201, f"Failed to create appointment: {create_resp.text}"
        appointment = create_resp.json()
        assert appointment["status"] == "SCHEDULED", "New appointments must start with SCHEDULED status."

        appointment_id = appointment["id"]

        # Modify appointment status to IN_PROGRESS (valid modification)
        mod_resp = modify_appointment_status(appointment_id, "IN_PROGRESS")
        assert mod_resp.status_code == 200, f"Failed to modify appointment status: {mod_resp.text}"
        mod_appt = mod_resp.json()
        assert mod_appt["status"] == "IN_PROGRESS", "Appointment status should be updated to IN_PROGRESS."

        # Attempt invalid status update - e.g., setting status to invalid string
        invalid_resp = modify_appointment_status(appointment_id, "INVALID_STATUS")
        assert invalid_resp.status_code == 400, "Invalid status update should be rejected with 400 error."

        # Attempt modification with missing required fields (patch with empty body)
        empty_resp = requests.patch(f"{BASE_URL}/api/appointments/{appointment_id}/", json={}, headers=HEADERS, timeout=TIMEOUT)
        # Depending on API design, empty patch may return 200 or 400 - check response
        assert empty_resp.status_code in (200, 400), "Empty PATCH request should be handled gracefully."

        # Cancel the appointment
        cancel_resp = cancel_appointment(appointment_id)
        assert cancel_resp.status_code == 200, f"Failed to cancel appointment: {cancel_resp.text}"
        cancelled_appt = cancel_resp.json()
        assert cancelled_appt["status"] == "CANCELLED", "Appointment status should be updated to CANCELLED."

        # Try to modify a cancelled appointment (should reject if business rule forbids)
        mod_after_cancel_resp = modify_appointment_status(appointment_id, "SCHEDULED")
        # Either 400 or 409 conflict expected if modification of cancelled appointment forbidden
        assert mod_after_cancel_resp.status_code in (400, 409), "Modification of cancelled appointment should be forbidden."

        # Validation test: attempt to modify appointment_date to past date (assuming allowed on modification)
        past_date = (datetime.now() - timedelta(days=1)).date().isoformat()
        patch_payload = {"appointment_date": past_date}
        invalid_date_resp = requests.patch(f"{BASE_URL}/api/appointments/{appointment_id}/", json=patch_payload, headers=HEADERS, timeout=TIMEOUT)
        # Validate the system rejects past date modification
        assert invalid_date_resp.status_code == 400, "Should reject modifying appointment to a past date."

    finally:
        # Clean up created appointment if exists
        if appointment and "id" in appointment:
            requests.delete(f"{BASE_URL}/api/appointments/{appointment['id']}/", timeout=TIMEOUT)
        # Clean up doctor and patient
        if doctor and "id" in doctor:
            delete_doctor(doctor["id"])
        if patient and "id" in patient:
            delete_patient(patient["id"])

test_appointment_modification_and_cancellation()
