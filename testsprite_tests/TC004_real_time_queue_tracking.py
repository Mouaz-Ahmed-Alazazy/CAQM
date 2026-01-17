import requests
import uuid
import time

BASE_URL = "http://localhost:9000"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}

def create_doctor():
    # Create a doctor profile with specialization and availability
    doctor_data = {
        "name": f"Dr_{uuid.uuid4().hex[:8]}",
        "email": f"dr{uuid.uuid4().hex[:8]}@clinic.com",
        "specialization": "General",
        "weekly_availability": [
            {"day": "Monday", "start_time": "09:00", "end_time": "17:00"},
            {"day": "Tuesday", "start_time": "09:00", "end_time": "17:00"}
        ]
    }
    resp = requests.post(f"{BASE_URL}/api/doctors/", json=doctor_data, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()['id']

def delete_doctor(doctor_id):
    requests.delete(f"{BASE_URL}/api/doctors/{doctor_id}/", headers=HEADERS, timeout=TIMEOUT)

def create_patient():
    # Create a patient profile with valid emergency contact
    patient_data = {
        "name": f"Patient_{uuid.uuid4().hex[:8]}",
        "email": f"patient{uuid.uuid4().hex[:8]}@example.com",
        "emergency_contact": "0911234567"
    }
    resp = requests.post(f"{BASE_URL}/api/patients/", json=patient_data, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()['id']

def delete_patient(patient_id):
    requests.delete(f"{BASE_URL}/api/patients/{patient_id}/", headers=HEADERS, timeout=TIMEOUT)

def book_appointment(patient_id, doctor_id):
    # Book a scheduled appointment for today in the future, simple valid appointment
    appointment_data = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_date": time.strftime("%Y-%m-%d"),
        "start_time": "15:00",
        "status": "SCHEDULED"
    }
    resp = requests.post(f"{BASE_URL}/api/appointments/", json=appointment_data, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()['id']

def cancel_appointment(appointment_id):
    requests.delete(f"{BASE_URL}/api/appointments/{appointment_id}/", headers=HEADERS, timeout=TIMEOUT)

def checkin_appointment(appointment_id):
    # Endpoint to perform digital check-in for walk-in or scheduled appointments
    resp = requests.post(f"{BASE_URL}/api/appointments/{appointment_id}/checkin/", headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def get_queue_status(doctor_id):
    # Get real-time queue tracking info for a doctor's patients
    resp = requests.get(f"{BASE_URL}/api/queues/{doctor_id}/", headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def test_real_time_queue_tracking():
    doctor_id = None
    patient1_id = None
    patient2_id = None
    appointment1_id = None
    appointment2_id = None
    try:
        # Create doctor and patients
        doctor_id = create_doctor()
        patient1_id = create_patient()
        patient2_id = create_patient()

        # Book two appointments for same doctor to test FIFO queue behavior
        appointment1_id = book_appointment(patient1_id, doctor_id)
        appointment2_id = book_appointment(patient2_id, doctor_id)

        # Check initial queue status: both patients in queue, patient1 ahead of patient2 (FIFO)
        queue_status = get_queue_status(doctor_id)
        assert isinstance(queue_status, dict), "Queue status response must be a dict"
        queue_list = queue_status.get("queue")
        assert isinstance(queue_list, list), "Queue list must be a list"
        # Expect at least two patients in queue and patient1 position before patient2
        positions = {entry["appointment_id"]: entry["position"] for entry in queue_list}
        assert appointment1_id in positions, "Patient 1 appointment not in queue"
        assert appointment2_id in positions, "Patient 2 appointment not in queue"
        assert positions[appointment1_id] < positions[appointment2_id], "FIFO order violated in queue"

        # Simulate patient1 check-in to update status to CHECKED_IN
        checkin_resp = checkin_appointment(appointment1_id)
        assert checkin_resp.get("status") == "CHECKED_IN", "Patient1 should be checked-in"

        # Queue should reflect update: patient1 now CHECKED_IN and position 1
        queue_status_updated = get_queue_status(doctor_id)
        queue_list_updated = queue_status_updated.get("queue")
        patient1_entry = next((q for q in queue_list_updated if q["appointment_id"] == appointment1_id), None)
        patient2_entry = next((q for q in queue_list_updated if q["appointment_id"] == appointment2_id), None)
        assert patient1_entry is not None and patient2_entry is not None, "Both patients should be in updated queue"
        # Patient1 position should remain ahead in queue
        assert patient1_entry["position"] < patient2_entry["position"], "Queue order not maintained after check-in"
        assert patient1_entry["status"] == "CHECKED_IN", "Patient1 status should be CHECKED_IN"

        # Simulate patient1 consultation start and end (status changes)
        resp_start = requests.post(f"{BASE_URL}/api/appointments/{appointment1_id}/start_consultation/", headers=HEADERS, timeout=TIMEOUT)
        resp_start.raise_for_status()
        resp_end = requests.post(f"{BASE_URL}/api/appointments/{appointment1_id}/end_consultation/", headers=HEADERS, timeout=TIMEOUT)
        resp_end.raise_for_status()

        # Queue updates after patient1 consultation ended, patient1 should be COMPLETED and patient2 moves up in position
        queue_status_post_consult = get_queue_status(doctor_id)
        queue_list_post = queue_status_post_consult.get("queue")

        # Patient1 should no longer be active in queue or have status COMPLETED
        patient1_post = next((q for q in queue_list_post if q["appointment_id"] == appointment1_id), None)
        patient2_post = next((q for q in queue_list_post if q["appointment_id"] == appointment2_id), None)
        
        if patient1_post:
            assert patient1_post["status"] == "COMPLETED", "Patient1 status should be COMPLETED after consultation"
        # Patient2 should have position 1 now
        assert patient2_post is not None, "Patient2 must be in queue after patient1 consultation ends"
        assert patient2_post["position"] == 1, "Patient2 position should be updated to 1 after patient1 consultation ends"

        # Check notification fields exist for queue entries (simulate notifications)
        for entry in queue_list_post:
            assert "notifications" in entry, "Queue entry must include notification info"
            notifications = entry["notifications"]
            assert isinstance(notifications, dict), "Notifications must be a dictionary"
            # Should at least have notification channels listed, e.g. in_app, email, sms
            for channel in ['in_app', 'email', 'sms']:
                assert channel in notifications, f"Notification channel '{channel}' missing"
                assert isinstance(notifications[channel], bool), f"Notification channel '{channel}' should be boolean"

    finally:
        # Cleanup all created resources
        if appointment1_id:
            cancel_appointment(appointment1_id)
        if appointment2_id:
            cancel_appointment(appointment2_id)
        if patient1_id:
            delete_patient(patient1_id)
        if patient2_id:
            delete_patient(patient2_id)
        if doctor_id:
            delete_doctor(doctor_id)

test_real_time_queue_tracking()