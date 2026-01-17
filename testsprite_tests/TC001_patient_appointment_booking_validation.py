import requests
from datetime import datetime, timedelta
import pytest

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

# Assuming we have API endpoints:
# POST /api/patients/          -> create patient
# DELETE /api/patients/{id}/   -> delete patient
# POST /api/doctors/           -> create doctor
# DELETE /api/doctors/{id}/    -> delete doctor
# POST /api/appointments/      -> book appointment
# DELETE /api/appointments/{id}/ -> delete appointment

HEADERS = {
    "Content-Type": "application/json",
    # Add authentication headers if needed, e.g.
    # "Authorization": "Bearer <token>",
}


def create_patient():
    payload = {
        "first_name": "Test",
        "last_name": "Patient",
        "email": f"test_patient_{datetime.utcnow().timestamp()}@example.com",
        "password": "TestPass123!",
        "emergency_contact": "0911234567"
    }
    resp = requests.post(f"{BASE_URL}/api/patients/", json=payload, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def delete_patient(patient_id):
    requests.delete(f"{BASE_URL}/api/patients/{patient_id}/", headers=HEADERS, timeout=TIMEOUT)


def create_doctor(specialization):
    payload = {
        "first_name": "Test",
        "last_name": "Doctor",
        "email": f"test_doctor_{specialization}_{datetime.utcnow().timestamp()}@example.com",
        "password": "TestPass123!",
        "specialization": specialization,
        # adding minimal required fields for doctor creation
        "availability": [
          {"day": "Monday", "start_time": "09:00", "end_time": "17:00"},
          {"day": "Tuesday", "start_time": "09:00", "end_time": "17:00"},
          {"day": "Wednesday", "start_time": "09:00", "end_time": "17:00"},
          {"day": "Thursday", "start_time": "09:00", "end_time": "17:00"},
          {"day": "Friday", "start_time": "09:00", "end_time": "17:00"}
        ]
    }
    resp = requests.post(f"{BASE_URL}/api/doctors/", json=payload, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def delete_doctor(doctor_id):
    requests.delete(f"{BASE_URL}/api/doctors/{doctor_id}/", headers=HEADERS, timeout=TIMEOUT)


def book_appointment(patient_id, doctor_id, appointment_date, start_time, specialization):
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "start_time": start_time,
        "specialization": specialization,
        "appointment_type": "SCHEDULED"
    }
    resp = requests.post(f"{BASE_URL}/api/appointments/", json=payload, headers=HEADERS, timeout=TIMEOUT)
    return resp


def delete_appointment(appointment_id):
    requests.delete(f"{BASE_URL}/api/appointments/{appointment_id}/", headers=HEADERS, timeout=TIMEOUT)


def test_patient_appointment_booking_validation():
    # Create test patient
    patient = create_patient()
    patient_id = patient["id"]

    # Create test doctor with specialization "Cardiology"
    doctor = create_doctor("Cardiology")
    doctor_id = doctor["id"]

    appointments_created = []
    try:
        today = datetime.utcnow().date()
        past_date = (today - timedelta(days=1)).isoformat()
        future_date = (today + timedelta(days=1)).isoformat()
        start_time = "10:00"

        # 1) Test booking an appointment for a past date (should fail)
        resp = book_appointment(patient_id, doctor_id, past_date, start_time, "Cardiology")
        assert resp.status_code == 400, "Booking appointment for past date should fail"
        assert "past date" in resp.text.lower() or "invalid" in resp.text.lower()

        # 2) Book first appointment for patient in Cardiology specialization on future_date (should succeed)
        resp = book_appointment(patient_id, doctor_id, future_date, start_time, "Cardiology")
        assert resp.status_code == 201, f"Expected 201 Created, got {resp.status_code}"
        appointment1 = resp.json()
        appointments_created.append(appointment1["id"])

        # 3) Attempt to book another appointment for the same patient, same specialization, same day (should fail)
        # Different doctor with same specialization (Create second doctor)
        doctor2 = create_doctor("Cardiology")
        doctor2_id = doctor2["id"]
        try:
            resp = book_appointment(patient_id, doctor2_id, future_date, "11:00", "Cardiology")
            assert resp.status_code == 400, "Should not allow multiple appointments for same specialization per day per patient"
            assert "one appointment per specialization" in resp.text.lower() or "already has an appointment" in resp.text.lower()
        finally:
            delete_doctor(doctor2_id)

        # 4) Book max 15 appointments for the doctor on the same date (different patients)
        for i in range(2, 17):  # already 1 appointment booked above, book next 15 to exceed limit
            new_patient = create_patient()
            p_id = new_patient["id"]
            try:
                time = (10 + (i - 2)) % 17  # ensure different hour slots if needed
                appointment_time = f"{time:02d}:00"
                resp = book_appointment(p_id, doctor_id, future_date, appointment_time, "Cardiology")
                if i <= 15:
                    # up to 15 appointments should succeed
                    assert resp.status_code == 201, f"Appointment {i} should be successful"
                    app_id = resp.json()["id"]
                    appointments_created.append(app_id)
                else:
                    # 16th appointment and above should fail
                    assert resp.status_code == 400, "Should enforce max 15 appointments per doctor per day"
                    assert "limit" in resp.text.lower() or "maximum" in resp.text.lower()
                    break
            finally:
                delete_patient(p_id)

    finally:
        # Cleanup appointments
        for app_id in appointments_created:
            try:
                delete_appointment(app_id)
            except Exception:
                pass
        # Cleanup patient and doctor
        delete_patient(patient_id)
        delete_doctor(doctor_id)


test_patient_appointment_booking_validation()