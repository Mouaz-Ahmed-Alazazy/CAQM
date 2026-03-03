import requests
import uuid
import datetime

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

# Authentication fixture replacement: simulate login to get auth token
def authenticate():
    # Example fixed test user (would normally be replaced by fixture or env var)
    login_url = f"{BASE_URL}/api/auth/login/"
    credentials = {"email": "testpatient@example.com", "password": "TestPassword123"}
    resp = requests.post(login_url, json=credentials, timeout=TIMEOUT)
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise Exception("Authentication failed: no access token received")
    return token

def create_doctor(headers):
    # Create a doctor for appointment creation (assuming API for doctor creation exists)
    doctor_url = f"{BASE_URL}/api/doctors/"
    doctor_data = {
        "name": f"Dr. Test {uuid.uuid4().hex[:6]}",
        "specialization": "General",
        "email": f"doctor{uuid.uuid4().hex[:6]}@clinic.test",
        "phone": "09123456789"
    }
    resp = requests.post(doctor_url, json=doctor_data, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()  # Expect contains 'id'

def create_patient(headers):
    # Create a patient for appointment creation (assuming API for patient creation exists)
    patient_url = f"{BASE_URL}/api/patients/"
    patient_data = {
        "first_name": "Test",
        "last_name": "Patient",
        "email": f"patient{uuid.uuid4().hex[:6]}@clinic.test",
        "phone": "09212345678",
        "emergency_contact": "09176543210",
        "date_of_birth": "1980-01-01",
        "gender": "M"
    }
    resp = requests.post(patient_url, json=patient_data, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()  # Expect contains 'id'

def create_appointment(headers, patient_id, doctor_id):
    # Book a scheduled appointment for tomorrow
    appointment_url = f"{BASE_URL}/api/appointments/"
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    appointment_data = {
        "patient": patient_id,
        "doctor": doctor_id,
        "appointment_date": tomorrow.isoformat(),
        "start_time": "09:00:00",
        "specialization": "General",
        "type": "SCHEDULED"
    }
    resp = requests.post(appointment_url, json=appointment_data, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()  # Expect contains 'id' and 'qr_code'

def get_qr_code(appointment_id, headers):
    # Fetch check-in info which includes QR code data by appointment ID
    checkin_url = f"{BASE_URL}/api/appointments/{appointment_id}/checkin_qrcode/"
    resp = requests.get(checkin_url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()  # Expect at least a field with QR code and appointment linkage data

def delete_appointment(appointment_id, headers):
    url = f"{BASE_URL}/api/appointments/{appointment_id}/"
    resp = requests.delete(url, headers=headers, timeout=TIMEOUT)
    if resp.status_code not in (204, 200):
        raise Exception(f"Failed to delete appointment id {appointment_id}")

def delete_doctor(doctor_id, headers):
    url = f"{BASE_URL}/api/doctors/{doctor_id}/"
    try:
        resp = requests.delete(url, headers=headers, timeout=TIMEOUT)
        if resp.status_code not in (204, 200):
            raise Exception(f"Failed to delete doctor id {doctor_id}")
    except Exception:
        pass

def delete_patient(patient_id, headers):
    url = f"{BASE_URL}/api/patients/{patient_id}/"
    try:
        resp = requests.delete(url, headers=headers, timeout=TIMEOUT)
        if resp.status_code not in (204, 200):
            raise Exception(f"Failed to delete patient id {patient_id}")
    except Exception:
        pass

def test_digital_checkin_qrcode_generation():
    token = authenticate()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    doctor = None
    patient = None
    appointment1 = None
    appointment2 = None

    try:
        doctor = create_doctor(headers)
        patient = create_patient(headers)

        # Create two different appointments for same patient and different times to check unique QR codes
        appointment1 = create_appointment(headers, patient["id"], doctor["id"])
        appointment2 = create_appointment(headers, patient["id"], doctor["id"])

        # Fetch QR codes for both appointments - expecting uniqueness and correct linkage
        qrcode1 = get_qr_code(appointment1["id"], headers)
        qrcode2 = get_qr_code(appointment2["id"], headers)

        # Validate QR code presence and uniqueness
        assert "qr_code" in qrcode1, "QR code missing in first appointment response"
        assert "qr_code" in qrcode2, "QR code missing in second appointment response"
        assert qrcode1["qr_code"] != qrcode2["qr_code"], "QR codes for different appointments should be unique"

        # Validate QR codes link back correctly to appointment and patient data
        assert qrcode1.get("appointment_id") == appointment1["id"], "QR code 1 appointment_id mismatch"
        assert qrcode1.get("patient_id") == patient["id"], "QR code 1 patient_id mismatch"
        assert qrcode2.get("appointment_id") == appointment2["id"], "QR code 2 appointment_id mismatch"
        assert qrcode2.get("patient_id") == patient["id"], "QR code 2 patient_id mismatch"

        # Validate QR codes format - assume string and non-empty
        assert isinstance(qrcode1["qr_code"], str) and len(qrcode1["qr_code"]) > 0, "Invalid QR code 1 format"
        assert isinstance(qrcode2["qr_code"], str) and len(qrcode2["qr_code"]) > 0, "Invalid QR code 2 format"

    finally:
        # Cleanup in reverse order
        if appointment1:
            try:
                delete_appointment(appointment1["id"], headers)
            except Exception:
                pass
        if appointment2:
            try:
                delete_appointment(appointment2["id"], headers)
            except Exception:
                pass
        if patient:
            delete_patient(patient["id"], headers)
        if doctor:
            delete_doctor(doctor["id"], headers)

test_digital_checkin_qrcode_generation()