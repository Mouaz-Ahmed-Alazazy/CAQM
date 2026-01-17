import requests
from datetime import datetime, timedelta
import random
import string

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

# Helpers to create unique values
def random_string(length=6):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def create_doctor():
    url = f"{BASE_URL}/api/doctors/"
    payload = {
        "name": "Doctor " + random_string(),
        "specialization": "General",
        "email": f"{random_string()}@hospital.com"
    }
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def delete_doctor(doctor_id):
    url = f"{BASE_URL}/api/doctors/{doctor_id}/"
    resp = requests.delete(url, timeout=TIMEOUT)
    return resp

def create_patient():
    url = f"{BASE_URL}/api/patients/"
    payload = {
        "name": "Patient " + random_string(),
        "email": f"{random_string()}@test.com",
        "emergency_contact": "0911234567",
    }
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def delete_patient(patient_id):
    url = f"{BASE_URL}/api/patients/{patient_id}/"
    resp = requests.delete(url, timeout=TIMEOUT)
    return resp

def create_doctor_availability(doctor_id, weekday, start_time, end_time):
    url = f"{BASE_URL}/api/doctors/{doctor_id}/availability/"
    payload = {
        "weekday": weekday,  # 0=Monday ... 6=Sunday
        "start_time": start_time,  # "09:00"
        "end_time": end_time       # "17:00"
    }
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def delete_doctor_availability(doctor_id, availability_id):
    url = f"{BASE_URL}/api/doctors/{doctor_id}/availability/{availability_id}/"
    resp = requests.delete(url, timeout=TIMEOUT)
    return resp

def create_appointment(doctor_id, patient_id, appointment_date, start_time):
    url = f"{BASE_URL}/api/appointments/"
    payload = {
        "doctor": doctor_id,
        "patient": patient_id,
        "appointment_date": appointment_date.strftime("%Y-%m-%d"),
        "start_time": start_time,
        "status": "SCHEDULED"
    }
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    return resp

def delete_appointment(appointment_id):
    url = f"{BASE_URL}/api/appointments/{appointment_id}/"
    resp = requests.delete(url, timeout=TIMEOUT)
    return resp

def test_doctor_availability_scheduling_limit():
    # Create doctor
    doctor = create_doctor()
    doctor_id = doctor["id"]

    # Create patient pool
    patients = []
    try:
        for _ in range(16):
            patient = create_patient()
            patients.append(patient)
        
        # Setup weekly availability for doctor: Monday 09:00-17:00
        availability = create_doctor_availability(doctor_id, weekday=0, start_time="09:00", end_time="17:00")
        availability_id = availability["id"]

        # Target appointment date: Next Monday
        today = datetime.now()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        appointment_date = (today + timedelta(days=days_ahead)).date()

        # Each appointment will start at 09:00, incremental 30 minutes slots (09:00, 09:30, 10:00, ...)
        appointment_duration_minutes = 30
        slots_count = 15  # max per day
        start_hour = 9
        start_minute = 0

        created_appointments_ids = []

        # Book 15 appointments successfully
        for i in range(slots_count):
            hour = start_hour + (start_minute + i * appointment_duration_minutes) // 60
            minute = (start_minute + i * appointment_duration_minutes) % 60
            start_time = f"{hour:02d}:{minute:02d}"

            resp = create_appointment(doctor_id, patients[i]["id"], appointment_date, start_time)
            assert resp.status_code == 201, f"Expected 201 Created but got {resp.status_code}"
            response_data = resp.json()
            assert response_data["doctor"] == doctor_id
            assert response_data["patient"] == patients[i]["id"]
            assert response_data["appointment_date"] == appointment_date.strftime("%Y-%m-%d")
            assert response_data["start_time"] == start_time
            assert response_data["status"] == "SCHEDULED"
            created_appointments_ids.append(response_data["id"])

        # Attempt to book the 16th appointment on the same day for the same doctor should fail
        hour = start_hour + (start_minute + slots_count * appointment_duration_minutes) // 60
        minute = (start_minute + slots_count * appointment_duration_minutes) % 60
        start_time = f"{hour:02d}:{minute:02d}"

        resp = create_appointment(doctor_id, patients[slots_count]["id"], appointment_date, start_time)
        assert resp.status_code == 400 or resp.status_code == 409, (
            f"Expected 400 Bad Request or 409 Conflict for exceeding max appointments, got {resp.status_code}"
        )
        error_data = resp.json()
        assert "limit" in str(error_data).lower() or "maximum" in str(error_data).lower()

        # Attempt to book outside the weekly availability (e.g. Sunday)
        sunday = appointment_date + timedelta(days=6)
        resp = create_appointment(doctor_id, patients[slots_count]["id"], sunday, "09:00")
        assert resp.status_code == 400, f"Expected 400 Bad Request booking outside availability, got {resp.status_code}"
        err = resp.json()
        assert "availability" in str(err).lower() or "schedule" in str(err).lower()

    finally:
        # Cleanup: delete all created appointments
        for appt_id in created_appointments_ids:
            delete_appointment(appt_id)

        # Cleanup patients
        for p in patients:
            try:
                delete_patient(p["id"])
            except Exception:
                pass

        # Cleanup doctor availability
        try:
            delete_doctor_availability(doctor_id, availability_id)
        except Exception:
            pass

        # Cleanup doctor
        delete_doctor(doctor_id)

test_doctor_availability_scheduling_limit()
