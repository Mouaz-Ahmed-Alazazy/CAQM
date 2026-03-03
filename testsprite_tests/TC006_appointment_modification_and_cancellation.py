import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

# For testing, use a placeholder auth token (replace with valid token)
AUTH_TOKEN = "Bearer test-token"

# Helper functions to create patient, doctor, and appointment resources as needed

def create_patient(session, patient_data):
    resp = session.post(f"{BASE_URL}/patients/", json=patient_data, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()  # Expected: {'id': ..., ...}

def delete_patient(session, patient_id):
    resp = session.delete(f"{BASE_URL}/patients/{patient_id}/", timeout=TIMEOUT)
    # Ignoring errors on cleanup

def create_doctor(session, doctor_data):
    resp = session.post(f"{BASE_URL}/doctors/", json=doctor_data, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def delete_doctor(session, doctor_id):
    resp = session.delete(f"{BASE_URL}/doctors/{doctor_id}/", timeout=TIMEOUT)
    # Ignoring errors on cleanup

def create_appointment(session, appointment_data):
    resp = session.post(f"{BASE_URL}/appointments/", json=appointment_data, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def modify_appointment(session, appointment_id, update_data):
    resp = session.put(f"{BASE_URL}/appointments/{appointment_id}/", json=update_data, timeout=TIMEOUT)
    return resp

def cancel_appointment(session, appointment_id):
    resp = session.delete(f"{BASE_URL}/appointments/{appointment_id}/", timeout=TIMEOUT)
    return resp

def get_appointment(session, appointment_id):
    resp = session.get(f"{BASE_URL}/appointments/{appointment_id}/", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def valid_appointment_payload(patient_id, doctor_id, specialization, date):
    return {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "specialization": specialization,
        "appointment_date": date.strftime("%Y-%m-%d"),
        "start_time": "10:00",
        "status": "SCHEDULED"
    }

def valid_patient_payload():
    return {
        "name": "Test Patient",
        "email": "test.patient@example.com",
        "emergency_contact": "0911234567"
    }

def valid_doctor_payload():
    return {
        "name": "Dr. John Doe",
        "email": "john.doe@example.com",
        "specialization": "Cardiology"
    }

def test_appointment_modification_and_cancellation():
    session = requests.Session()
    session.headers.update({"Authorization": AUTH_TOKEN})
    patient = doctor = appointment = None
    # Setup patient
    try:
        patient = create_patient(session, valid_patient_payload())
        doctor = create_doctor(session, valid_doctor_payload())
        appointment_date = datetime.now() + timedelta(days=1)
        # Create appointment
        appointment_payload = valid_appointment_payload(
            patient['id'], doctor['id'], doctor['specialization'], appointment_date
        )
        appointment = create_appointment(session, appointment_payload)

        appointment_id = appointment['id']

        # 1. Verify initial status SCHEDULED
        appt_data = get_appointment(session, appointment_id)
        assert appt_data['status'] == "SCHEDULED"
        assert appt_data['patient_id'] == patient['id']
        assert appt_data['doctor_id'] == doctor['id']

        # 2. Modify appointment status to IN_PROGRESS (valid transition)
        update_resp = modify_appointment(session, appointment_id, {"status": "IN_PROGRESS"})
        assert update_resp.status_code == 200
        updated_data = update_resp.json()
        assert updated_data['status'] == "IN_PROGRESS"

        # 3. Modify appointment status to COMPLETED
        update_resp2 = modify_appointment(session, appointment_id, {"status": "COMPLETED"})
        assert update_resp2.status_code == 200
        updated_data2 = update_resp2.json()
        assert updated_data2['status'] == "COMPLETED"

        # 4. Attempt invalid status transition (e.g. COMPLETED back to SCHEDULED)
        update_resp_invalid = modify_appointment(session, appointment_id, {"status": "SCHEDULED"})
        assert update_resp_invalid.status_code == 400 or update_resp_invalid.status_code == 422

        # 5. Attempt to cancel completed appointment (should be forbidden)
        cancel_resp = cancel_appointment(session, appointment_id)
        assert cancel_resp.status_code == 400 or cancel_resp.status_code == 403

        # 6. Create another appointment to test cancellation flow
        appointment2_payload = valid_appointment_payload(
            patient['id'], doctor['id'], doctor['specialization'], appointment_date + timedelta(days=1)
        )
        appointment2 = create_appointment(session, appointment2_payload)
        appt2_id = appointment2['id']

        # Cancel this appointment successfully
        cancel_resp2 = cancel_appointment(session, appt2_id)
        assert cancel_resp2.status_code == 204 or cancel_resp2.status_code == 200

        # After cancellation, verify appointment is gone or marked cancelled
        resp_post_cancel = session.get(f"{BASE_URL}/appointments/{appt2_id}/", timeout=TIMEOUT)
        if resp_post_cancel.status_code == 404:
            # Appointment deleted
            pass
        else:
            # If not deleted, check status is CANCELLED
            data_post_cancel = resp_post_cancel.json()
            assert data_post_cancel['status'] == "CANCELLED"

        # 7. Validation rule enforcement: try to change appointment date to past
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        invalid_update = {"appointment_date": past_date}
        invalid_resp = modify_appointment(session, appointment_id, invalid_update)
        assert invalid_resp.status_code == 400 or invalid_resp.status_code == 422

        # 8. Validation rule enforcement: try to double book patient for same specialization same day
        # Create a new appointment with same patient/specialization/date - should error
        duplicate_appt_payload = valid_appointment_payload(
            patient['id'], doctor['id'], doctor['specialization'], appointment_date
        )
        dup_resp = session.post(f"{BASE_URL}/appointments/", json=duplicate_appt_payload, timeout=TIMEOUT)
        assert dup_resp.status_code == 400 or dup_resp.status_code == 422

    finally:
        # Cleanup created resources
        if appointment and 'id' in appointment:
            try:
                session.delete(f"{BASE_URL}/appointments/{appointment['id']}/", timeout=TIMEOUT)
            except Exception:
                pass
        if doctor and 'id' in doctor:
            try:
                delete_doctor(session, doctor['id'])
            except Exception:
                pass
        if patient and 'id' in patient:
            try:
                delete_patient(session, patient['id'])
            except Exception:
                pass

test_appointment_modification_and_cancellation()
