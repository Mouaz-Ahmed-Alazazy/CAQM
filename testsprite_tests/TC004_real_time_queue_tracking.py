import requests
import time

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

def create_doctor(specialization="General"):
    payload = {
        "name": "Dr. Test",
        "specialization": specialization,
        "weekly_availability": {
            "Monday": [["09:00", "17:00"]],
            "Tuesday": [["09:00", "17:00"]],
            "Wednesday": [["09:00", "17:00"]],
            "Thursday": [["09:00", "17:00"]],
            "Friday": [["09:00", "17:00"]],
        }
    }
    r = requests.post(f"{BASE_URL}/api/doctors/", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def delete_doctor(doctor_id):
    requests.delete(f"{BASE_URL}/api/doctors/{doctor_id}/", timeout=TIMEOUT)

def create_patient():
    payload = {
        "name": "Test Patient",
        "email": f"patient{int(time.time()*1000)}@test.com",
        "emergency_contact": "09112345678"
    }
    r = requests.post(f"{BASE_URL}/api/patients/", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def delete_patient(patient_id):
    requests.delete(f"{BASE_URL}/api/patients/{patient_id}/", timeout=TIMEOUT)

def create_appointment(doctor_id, patient_id, specialization="General", appointment_date=None, start_time="09:00"):
    if appointment_date is None:
        appointment_date = time.strftime("%Y-%m-%d", time.localtime(time.time() + 86400))  # tomorrow
    payload = {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "specialization": specialization,
        "appointment_date": appointment_date,
        "start_time": start_time,
        "type": "scheduled"  # scheduled appointment
    }
    r = requests.post(f"{BASE_URL}/api/appointments/", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def delete_appointment(appointment_id):
    requests.delete(f"{BASE_URL}/api/appointments/{appointment_id}/", timeout=TIMEOUT)

def get_queue_status(doctor_id):
    r = requests.get(f"{BASE_URL}/api/queues/{doctor_id}/", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def update_appointment_status(appointment_id, status):
    payload = {"status": status}
    r = requests.put(f"{BASE_URL}/api/appointments/{appointment_id}/status/", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def test_real_time_queue_tracking():
    """
    Validate the queue tracking API provides real-time updates on patient queue status and position,
    ensuring FIFO order management and notifications.
    """
    # Setup: create doctor and patient, create multiple appointments to simulate queue
    doctor = create_doctor()
    patient1 = create_patient()
    patient2 = create_patient()

    appointment_date = time.strftime("%Y-%m-%d", time.localtime(time.time() + 86400))  # tomorrow

    appointments = []
    try:
        appt1 = create_appointment(doctor_id=doctor["id"], patient_id=patient1["id"], appointment_date=appointment_date, start_time="09:00")
        appt2 = create_appointment(doctor_id=doctor["id"], patient_id=patient2["id"], appointment_date=appointment_date, start_time="09:15")
        appointments.extend([appt1, appt2])

        # Initially, queue should reflect appointment order by start_time (FIFO)
        queue_status = get_queue_status(doctor["id"])
        # Validate queue is ordered by start_time ascending
        appointment_ids_in_queue = [item["appointment_id"] for item in queue_status.get("queue", [])]
        assert appt1["id"] in appointment_ids_in_queue
        assert appt2["id"] in appointment_ids_in_queue
        assert appointment_ids_in_queue.index(appt1["id"]) < appointment_ids_in_queue.index(appt2["id"]), "FIFO order violated"

        # Validate each queue item has valid status and position
        for idx, item in enumerate(queue_status.get("queue", []), start=1):
            assert "status" in item
            assert "appointment_id" in item
            assert item["position"] == idx

        # Simulate patient1 checking in to move status forward and check queue updates
        update_appointment_status(appt1["id"], "CHECKED_IN")
        time.sleep(1)  # wait briefly for queue to update

        # After patient1 checked in, verify queue status updates accordingly
        queue_status_after_checkin = get_queue_status(doctor["id"])
        appt1_position = None
        appt1_status = None
        appt2_position = None
        appt2_status = None
        for item in queue_status_after_checkin.get("queue", []):
            if item["appointment_id"] == appt1["id"]:
                appt1_position = item["position"]
                appt1_status = item["status"]
            if item["appointment_id"] == appt2["id"]:
                appt2_position = item["position"]
                appt2_status = item["status"]

        # Patient1 should be at front or in-progress in the queue (position 1)
        assert appt1_position == 1
        assert appt1_status in ["CHECKED_IN", "IN_PROGRESS"]
        # Patient2 should be next in line (position 2)
        assert appt2_position == 2
        assert appt2_status == "SCHEDULED"

        # Simulate patient1 moving to IN_PROGRESS and completing consultation to test queue updates and notifications
        update_appointment_status(appt1["id"], "IN_PROGRESS")
        time.sleep(1)
        queue_status_in_progress = get_queue_status(doctor["id"])
        # Patient1 still position 1, status IN_PROGRESS
        found_appt1 = next((i for i in queue_status_in_progress.get("queue", []) if i["appointment_id"] == appt1["id"]), None)
        assert found_appt1 is not None
        assert found_appt1["status"] == "IN_PROGRESS"
        assert found_appt1["position"] == 1

        # Patient2 still position 2, status SCHEDULED
        found_appt2 = next((i for i in queue_status_in_progress.get("queue", []) if i["appointment_id"] == appt2["id"]), None)
        assert found_appt2 is not None
        assert found_appt2["status"] == "SCHEDULED"
        assert found_appt2["position"] == 2

        # Complete patient1 appointment to remove from queue
        update_appointment_status(appt1["id"], "COMPLETED")
        time.sleep(1)
        queue_status_completed = get_queue_status(doctor["id"])
        # Patient1 should no longer be in the queue
        appointment_ids = [item["appointment_id"] for item in queue_status_completed.get("queue", [])]
        assert appt1["id"] not in appointment_ids
        # Patient2 should now be position 1 and possibly notified (notification check via API)
        found_appt2_post = next((i for i in queue_status_completed.get("queue", []) if i["appointment_id"] == appt2["id"]), None)
        assert found_appt2_post is not None
        assert found_appt2_post["position"] == 1

        # Optionally check notifications endpoint for patient2
        r = requests.get(f"{BASE_URL}/api/notifications/?patient_id={patient2['id']}", timeout=TIMEOUT)
        r.raise_for_status()
        notifications = r.json().get("notifications", [])
        # Assert at least one notification related to queue position or status update for patient2
        notif_found = any(
            ("queue" in n.get("type", "").lower() or "appointment" in n.get("message", "").lower())
            for n in notifications
        )
        assert notif_found, "Expected queue-related notification for patient2"

    finally:
        # Cleanup: delete all created appointments, patients, and doctor
        for appt in appointments:
            try:
                delete_appointment(appt["id"])
            except Exception:
                pass
        try:
            delete_patient(patient1["id"])
        except Exception:
            pass
        try:
            delete_patient(patient2["id"])
        except Exception:
            pass
        try:
            delete_doctor(doctor["id"])
        except Exception:
            pass

test_real_time_queue_tracking()
