import requests
import pytest

BASE_URL = "http://localhost:9000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}
FEEDBACK_ENDPOINT = f"{BASE_URL}/api/patient-feedback/"

def create_dummy_doctor():
    url = f"{BASE_URL}/api/doctors/"
    payload = {
        "name": "Dr. Test Doctor",
        "specialization": "General",
        "email": "doctor.test@example.com"
    }
    resp = requests.post(url, json=payload, timeout=TIMEOUT, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()["id"]

def delete_dummy_doctor(doctor_id):
    url = f"{BASE_URL}/api/doctors/{doctor_id}/"
    requests.delete(url, timeout=TIMEOUT, headers=HEADERS)

def create_dummy_patient():
    url = f"{BASE_URL}/api/patients/"
    payload = {
        "name": "Test Patient",
        "email": "patient.test@example.com",
        "emergency_contact": "0911234567"
    }
    resp = requests.post(url, json=payload, timeout=TIMEOUT, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()["id"]

def delete_dummy_patient(patient_id):
    url = f"{BASE_URL}/api/patients/{patient_id}/"
    requests.delete(url, timeout=TIMEOUT, headers=HEADERS)


def test_patient_feedback_submission():
    # Setup: create doctor and patient needed for feedback
    doctor_id = None
    patient_id = None
    try:
        doctor_id = create_dummy_doctor()
        patient_id = create_dummy_patient()

        valid_feedback_payload = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "rating": 5,
            "feedback_text": "Excellent care and attention.",
            "clinic_service_rating": 4
        }

        # Positive test: submit valid feedback
        response = requests.post(FEEDBACK_ENDPOINT, json=valid_feedback_payload, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}"
        data = response.json()
        assert "id" in data, "Response missing feedback id"
        assert data["rating"] == 5
        assert data["clinic_service_rating"] == 4
        assert data["feedback_text"] == "Excellent care and attention."
        assert data["doctor_id"] == doctor_id
        assert data["patient_id"] == patient_id

        # Negative tests for required fields validation:
        # Missing patient_id
        payload_missing_patient = valid_feedback_payload.copy()
        del payload_missing_patient["patient_id"]
        response = requests.post(FEEDBACK_ENDPOINT, json=payload_missing_patient, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 400
        assert "patient_id" in response.text or "patient" in response.text

        # Missing doctor_id
        payload_missing_doctor = valid_feedback_payload.copy()
        del payload_missing_doctor["doctor_id"]
        response = requests.post(FEEDBACK_ENDPOINT, json=payload_missing_doctor, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 400
        assert "doctor_id" in response.text or "doctor" in response.text

        # Missing rating
        payload_missing_rating = valid_feedback_payload.copy()
        del payload_missing_rating["rating"]
        response = requests.post(FEEDBACK_ENDPOINT, json=payload_missing_rating, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 400
        assert "rating" in response.text

        # Rating out of accepted range (assuming 1-5)
        payload_invalid_rating = valid_feedback_payload.copy()
        payload_invalid_rating["rating"] = 6
        response = requests.post(FEEDBACK_ENDPOINT, json=payload_invalid_rating, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 400
        assert "rating" in response.text or "invalid" in response.text.lower()

        # Missing clinic_service_rating (assuming required)
        payload_missing_clinic_rating = valid_feedback_payload.copy()
        del payload_missing_clinic_rating["clinic_service_rating"]
        response = requests.post(FEEDBACK_ENDPOINT, json=payload_missing_clinic_rating, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 400
        assert "clinic_service_rating" in response.text

        # Feedback text optional: test empty feedback_text allowed if API design permits
        payload_no_feedback_text = valid_feedback_payload.copy()
        payload_no_feedback_text["feedback_text"] = ""
        response = requests.post(FEEDBACK_ENDPOINT, json=payload_no_feedback_text, headers=HEADERS, timeout=TIMEOUT)
        # Accept either success or validation failure depending on API design - here assume success allowed
        assert response.status_code in (200, 201)

    finally:
        if patient_id:
            delete_dummy_patient(patient_id)
        if doctor_id:
            delete_dummy_doctor(doctor_id)

test_patient_feedback_submission()