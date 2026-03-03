import requests
import datetime
import pytest

BASE_URL = "http://localhost:9000"
TIMEOUT = 30
HEADERS = {'Content-Type': 'application/json'}

def create_patient():
    url = f"{BASE_URL}/patients/"
    data = {
        "name": "Test Patient",
        "email": f"test.patient{datetime.datetime.utcnow().timestamp()}@example.com",
        "password": "TestPass123!",
        "emergency_contact": "0911234567"
    }
    response = requests.post(url, json=data, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()

def delete_patient(patient_id):
    url = f"{BASE_URL}/patients/{patient_id}/"
    response = requests.delete(url, headers=HEADERS, timeout=TIMEOUT)
    if response.status_code not in (204, 404):
        response.raise_for_status()

def create_doctor(specialization="Cardiology"):
    url = f"{BASE_URL}/doctors/"
    data = {
        "name": f"Dr Test {specialization}",
        "email": f"dr.{specialization.lower()}{datetime.datetime.utcnow().timestamp()}@example.com",
        "specialization": specialization,
        "password": "DocPass123!"
    }
    response = requests.post(url, json=data, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()

def delete_doctor(doctor_id):
    url = f"{BASE_URL}/doctors/{doctor_id}/"
    response = requests.delete(url, headers=HEADERS, timeout=TIMEOUT)
    if response.status_code not in (204, 404):
        response.raise_for_status()

def create_appointment(payload):
    url = f"{BASE_URL}/appointments/"
    response = requests.post(url, json=payload, headers=HEADERS, timeout=TIMEOUT)
    return response

def delete_appointment(appointment_id):
    url = f"{BASE_URL}/appointments/{appointment_id}/"
    response = requests.delete(url, headers=HEADERS, timeout=TIMEOUT)
    if response.status_code not in (204, 404):
        response.raise_for_status()

def test_patient_appointment_booking_validation():
    # Setup patient and doctor
    patient = None
    doctor = None
    created_appointments = []
    try:
        patient = create_patient()
        doctor = create_doctor(specialization="Cardiology")

        patient_id = patient['id']
        doctor_id = doctor['id']
        specialization = doctor['specialization']

        # 1. Test booking appointment for past date - should reject
        past_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        payload_past = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "specialization": specialization,
            "appointment_date": past_date,
            "start_time": "10:00",
            "status": "SCHEDULED"
        }
        resp_past = create_appointment(payload_past)
        assert resp_past.status_code == 400 or resp_past.status_code == 422
        assert "past" in resp_past.text.lower()

        # 2. Book one valid appointment for today
        today_date = datetime.date.today().isoformat()
        payload_valid = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "specialization": specialization,
            "appointment_date": today_date,
            "start_time": "10:00",
            "status": "SCHEDULED"
        }
        resp_valid = create_appointment(payload_valid)
        assert resp_valid.status_code == 201
        appointment1 = resp_valid.json()
        created_appointments.append(appointment1['id'])

        # 3. Attempt to book a second appointment for the same patient, same specialization, same day - should reject
        payload_dup_spec = payload_valid.copy()
        payload_dup_spec["start_time"] = "11:00"  # different time but same day and specialization
        resp_dup_spec = create_appointment(payload_dup_spec)
        assert resp_dup_spec.status_code == 400 or resp_dup_spec.status_code == 422
        assert "one appointment per specialization per day" in resp_dup_spec.text.lower() or "already exists" in resp_dup_spec.text.lower()

        # 4. Book up to 15 appointments for the same doctor, different patients or times
        for i in range(2, 17):  # Already booked 1, now booking up to 16 to test limit
            # Create different patient for each appointment after first
            if i > 1:
                new_patient = create_patient()
                created_patient_id = new_patient['id']
            else:
                created_patient_id = patient_id

            payload_limit = {
                "patient_id": created_patient_id,
                "doctor_id": doctor_id,
                "specialization": specialization,
                "appointment_date": today_date,
                "start_time": f"{10 + i}:00",  # Different hour to avoid time collisions
                "status": "SCHEDULED"
            }
            resp_limit = create_appointment(payload_limit)
            if i <= 15:
                # Should succeed for first 15 appointments total per doctor per day
                assert resp_limit.status_code == 201
                appointment_created = resp_limit.json()
                created_appointments.append(appointment_created['id'])
            else:
                # This should fail - over 15 appointments
                assert resp_limit.status_code == 400 or resp_limit.status_code == 422
                assert "15 appointments" in resp_limit.text.lower() or "daily limit" in resp_limit.text.lower()

    finally:
        # Cleanup created resources
        for appt_id in created_appointments:
            try:
                delete_appointment(appt_id)
            except Exception:
                pass
        if patient:
            try:
                delete_patient(patient['id'])
            except Exception:
                pass
        if doctor:
            try:
                delete_doctor(doctor['id'])
            except Exception:
                pass

test_patient_appointment_booking_validation()