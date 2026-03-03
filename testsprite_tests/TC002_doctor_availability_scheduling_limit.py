import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

# Helper functions for creating and deleting doctor, patient, and appointments

def create_doctor(session, doctor_payload):
    resp = session.post(f"{BASE_URL}/api/doctors/", json=doctor_payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def delete_doctor(session, doctor_id):
    resp = session.delete(f"{BASE_URL}/api/doctors/{doctor_id}/", timeout=TIMEOUT)
    return resp.status_code == 204

def create_patient(session, patient_payload):
    resp = session.post(f"{BASE_URL}/api/patients/", json=patient_payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def delete_patient(session, patient_id):
    resp = session.delete(f"{BASE_URL}/api/patients/{patient_id}/", timeout=TIMEOUT)
    return resp.status_code == 204

def create_appointment(session, appointment_payload):
    resp = session.post(f"{BASE_URL}/api/appointments/", json=appointment_payload, timeout=TIMEOUT)
    return resp

def delete_appointment(session, appointment_id):
    resp = session.delete(f"{BASE_URL}/api/appointments/{appointment_id}/", timeout=TIMEOUT)
    return resp.status_code == 204

def create_doctor_availability(session, doctor_id, availability_payload):
    resp = session.post(f"{BASE_URL}/api/doctors/{doctor_id}/availability/", json=availability_payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def delete_doctor_availability(session, availability_id):
    resp = session.delete(f"{BASE_URL}/api/doctoravailability/{availability_id}/", timeout=TIMEOUT)
    return resp.status_code == 204


def test_doctor_availability_scheduling_limit():
    session = requests.Session()
    created_appointments = []
    created_availability = []
    try:
        # Create a test doctor with a specialization and weekly availability respecting the schema
        doctor_payload = {
            "name": "Dr. Test",
            "specialization": "General",
            "email": "drtest@example.com",
            "phone": "0921234567"
        }
        doctor = create_doctor(session, doctor_payload)
        doctor_id = doctor["id"]

        # Setup weekly availability: allow availability Mon-Fri 9am-5pm with 1-hour slots (simulate)
        # Assuming availability schema requires day_of_week (0=Mon,...6=Sun), start_time, end_time in HH:MM format
        availability_slots = []
        for day in range(5):  # Monday(0) to Friday(4)
            availability_payload = {
                "day_of_week": day,
                "start_time": "09:00",
                "end_time": "17:00"
            }
            avail = create_doctor_availability(session, doctor_id, availability_payload)
            created_availability.append(avail["id"])
            availability_slots.append(avail)

        # Create a patient to book appointments
        patient_payload = {
            "name": "Patient Test",
            "email": "patienttest@example.com",
            "emergency_contact": "0917654321"
        }
        patient = create_patient(session, patient_payload)
        patient_id = patient["id"]

        # Book 15 appointments for the doctor on a future date (limit)
        appointment_date = (datetime.now() + timedelta(days=7)).date().isoformat()
        for i in range(15):
            appointment_payload = {
                "doctor_id": doctor_id,
                "patient_id": patient_id,
                "appointment_date": appointment_date,
                "start_time": f"{9 + i % 8}:00",  # spread hours 9:00-16:00 (cycling)
                "specialization": doctor_payload["specialization"],
                "status": "SCHEDULED"
            }
            resp = create_appointment(session, appointment_payload)
            assert resp.status_code == 201, f"Failed to create appointment {i+1}, response: {resp.text}"
            created_appointments.append(resp.json()["id"])

        # Attempt to book the 16th appointment on the same day - should fail with 400 or suitable error
        appointment_payload = {
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "appointment_date": appointment_date,
            "start_time": "17:00",
            "specialization": doctor_payload["specialization"],
            "status": "SCHEDULED"
        }
        resp = create_appointment(session, appointment_payload)
        assert resp.status_code == 400 or resp.status_code == 403, (
            "API did not enforce maximum 15 appointments per day limit"
        )
        # Error message validation (if exists)
        if resp.status_code == 400:
            json_resp = resp.json()
            assert "maximum" in str(json_resp).lower() or "limit" in str(json_resp).lower()

        # Attempt to book appointment outside availability time (e.g., 18:00) should fail
        appointment_payload_outside_time = {
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "appointment_date": appointment_date,
            "start_time": "18:00",  # Outside 9-17 availability
            "specialization": doctor_payload["specialization"],
            "status": "SCHEDULED"
        }
        resp = create_appointment(session, appointment_payload_outside_time)
        assert resp.status_code == 400 or resp.status_code == 403, (
            "API allowed appointment outside doctor's weekly availability"
        )
        if resp.status_code == 400:
            json_resp = resp.json()
            assert "availability" in str(json_resp).lower() or "time slot" in str(json_resp).lower()

    finally:
        # Clean up appointments
        for appt_id in created_appointments:
            delete_appointment(session, appt_id)
        # Clean up availability
        for avail_id in created_availability:
            delete_doctor_availability(session, avail_id)
        # Clean up patient and doctor
        if 'patient_id' in locals():
            delete_patient(session, patient_id)
        if 'doctor_id' in locals():
            delete_doctor(session, doctor_id)

test_doctor_availability_scheduling_limit()
