import requests
import uuid
import datetime

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

# Helper functions to create and delete resources for test
def create_doctor():
    url = f"{BASE_URL}/doctors/"
    doctor_data = {
        "name": f"Dr. Test {uuid.uuid4()}",
        "specialization": "General"
    }
    resp = requests.post(url, json=doctor_data, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def delete_doctor(doctor_id):
    url = f"{BASE_URL}/doctors/{doctor_id}/"
    resp = requests.delete(url, timeout=TIMEOUT)
    # ignore errors on delete

def create_patient():
    url = f"{BASE_URL}/patients/"
    patient_data = {
        "name": f"Patient Test {uuid.uuid4()}",
        "email": f"patient_{uuid.uuid4().hex[:8]}@example.com",
        "emergency_contact": "0911234567"
    }
    resp = requests.post(url, json=patient_data, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def delete_patient(patient_id):
    url = f"{BASE_URL}/patients/{patient_id}/"
    resp = requests.delete(url, timeout=TIMEOUT)
    # ignore errors on delete

def create_appointment(patient_id, doctor_id, appointment_date):
    url = f"{BASE_URL}/appointments/"
    start_time = "10:00"
    appointment_payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "start_time": start_time,
        "type": "SCHEDULED"  # Assuming type field exists and SCHEDULED appointments are allowed
    }
    resp = requests.post(url, json=appointment_payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def delete_appointment(appointment_id):
    url = f"{BASE_URL}/appointments/{appointment_id}/"
    resp = requests.delete(url, timeout=TIMEOUT)
    # ignore errors on delete

def test_digital_checkin_qrcode_generation():
    doctor = create_doctor()
    patient = create_patient()
    appointment_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    appointment1 = None
    appointment2 = None
    try:
        # Create first appointment
        appointment1 = create_appointment(patient["id"], doctor["id"], appointment_date)
        # Create second appointment with same patient, doctor but different start_time to simulate different appointment
        # We must avoid unique constraint on (doctor, appointment_date, start_time), so change start_time for 2nd appt
        url = f"{BASE_URL}/appointments/"
        appointment_payload_2 = {
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "appointment_date": appointment_date,
            "start_time": "11:00",
            "type": "SCHEDULED"
        }
        resp = requests.post(url, json=appointment_payload_2, timeout=TIMEOUT)
        resp.raise_for_status()
        appointment2 = resp.json()

        # Fetch QR code for first appointment digital check-in
        qrcode_url_1 = f"{BASE_URL}/appointments/{appointment1['id']}/qrcode/"
        resp_qr1 = requests.get(qrcode_url_1, timeout=TIMEOUT)
        assert resp_qr1.status_code == 200
        qr_code_data_1 = resp_qr1.json()
        assert "qr_code" in qr_code_data_1 and qr_code_data_1["qr_code"], "QR code missing for appointment 1"

        # Fetch QR code for second appointment digital check-in
        qrcode_url_2 = f"{BASE_URL}/appointments/{appointment2['id']}/qrcode/"
        resp_qr2 = requests.get(qrcode_url_2, timeout=TIMEOUT)
        assert resp_qr2.status_code == 200
        qr_code_data_2 = resp_qr2.json()
        assert "qr_code" in qr_code_data_2 and qr_code_data_2["qr_code"], "QR code missing for appointment 2"

        # Confirm QR codes are unique
        assert qr_code_data_1["qr_code"] != qr_code_data_2["qr_code"], "QR codes should be unique per appointment"

        # Check the QR codes are linked correctly by scanning back appointment info with digital check-in API
        checkin_url_1 = f"{BASE_URL}/digital_checkin/scan/"
        payload1 = {"qr_code": qr_code_data_1["qr_code"]}
        resp_checkin1 = requests.post(checkin_url_1, json=payload1, timeout=TIMEOUT)
        assert resp_checkin1.status_code == 200
        checkin_data1 = resp_checkin1.json()
        assert checkin_data1["appointment_id"] == appointment1["id"]
        assert checkin_data1["patient_id"] == patient["id"]
        assert checkin_data1["doctor_id"] == doctor["id"]

        payload2 = {"qr_code": qr_code_data_2["qr_code"]}
        resp_checkin2 = requests.post(checkin_url_1, json=payload2, timeout=TIMEOUT)
        assert resp_checkin2.status_code == 200
        checkin_data2 = resp_checkin2.json()
        assert checkin_data2["appointment_id"] == appointment2["id"]
        assert checkin_data2["patient_id"] == patient["id"]
        assert checkin_data2["doctor_id"] == doctor["id"]

    finally:
        if appointment1:
            delete_appointment(appointment1["id"])
        if appointment2:
            delete_appointment(appointment2["id"])
        delete_patient(patient["id"])
        delete_doctor(doctor["id"])

test_digital_checkin_qrcode_generation()