import requests

BASE_URL = "http://localhost:9000"
TIMEOUT = 30

def test_patient_feedback_submission():
    headers = {
        "Content-Type": "application/json",
    }

    feedback_url = f"{BASE_URL}/api/patients/feedback/"

    # Use fixed patient_id and doctor_id since creation endpoints do not exist or are inaccessible
    patient_id = 1
    doctor_id = 1
    feedback_id = None

    try:
        # 1) Test successful feedback submission with all required fields
        feedback_payload = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "rating": 4,
            "service_rating": 5,
            "feedback_text": "The doctor provided excellent care and the clinic was very efficient."
        }

        feedback_resp = requests.post(feedback_url, json=feedback_payload, headers=headers, timeout=TIMEOUT)
        assert feedback_resp.status_code == 201, f"Failed to submit feedback: {feedback_resp.text}"
        feedback_data = feedback_resp.json()
        feedback_id = feedback_data.get("id")
        assert feedback_id is not None, "Feedback ID not returned"
        # Validate returned feedback data matches input where applicable
        assert feedback_data.get("patient_id") == patient_id
        assert feedback_data.get("doctor_id") == doctor_id
        assert feedback_data.get("rating") == feedback_payload["rating"]
        assert feedback_data.get("service_rating") == feedback_payload["service_rating"]
        assert feedback_data.get("feedback_text") == feedback_payload["feedback_text"]

        # 2) Test validation: missing required field patient_id
        invalid_payload_1 = {
            "doctor_id": doctor_id,
            "rating": 4,
            "service_rating": 5,
            "feedback_text": "Some feedback"
        }
        resp_invalid_1 = requests.post(feedback_url, json=invalid_payload_1, headers=headers, timeout=TIMEOUT)
        assert resp_invalid_1.status_code == 400, "Expected 400 error for missing patient_id"
        assert "patient_id" in resp_invalid_1.text.lower()

        # 3) Test validation: missing rating
        invalid_payload_2 = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "service_rating": 5,
            "feedback_text": "Some feedback"
        }
        resp_invalid_2 = requests.post(feedback_url, json=invalid_payload_2, headers=headers, timeout=TIMEOUT)
        assert resp_invalid_2.status_code == 400, "Expected 400 error for missing rating"
        assert "rating" in resp_invalid_2.text.lower()

        # 4) Test validation: rating out of allowed range (e.g., 0)
        invalid_payload_3 = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "rating": 0,
            "service_rating": 5,
            "feedback_text": "Invalid rating low"
        }
        resp_invalid_3 = requests.post(feedback_url, json=invalid_payload_3, headers=headers, timeout=TIMEOUT)
        assert resp_invalid_3.status_code == 400, "Expected 400 error for rating out of range"
        assert "rating" in resp_invalid_3.text.lower()

        # 5) Test validation: rating out of allowed range (e.g., 6)
        invalid_payload_4 = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "rating": 6,
            "service_rating": 5,
            "feedback_text": "Invalid rating high"
        }
        resp_invalid_4 = requests.post(feedback_url, json=invalid_payload_4, headers=headers, timeout=TIMEOUT)
        assert resp_invalid_4.status_code == 400, "Expected 400 error for rating out of range"
        assert "rating" in resp_invalid_4.text.lower()

        # 6) Test validation: missing service_rating
        invalid_payload_5 = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "rating": 4,
            "feedback_text": "Missing service rating"
        }
        resp_invalid_5 = requests.post(feedback_url, json=invalid_payload_5, headers=headers, timeout=TIMEOUT)
        assert resp_invalid_5.status_code == 400, "Expected 400 error for missing service_rating"
        assert "service_rating" in resp_invalid_5.text.lower()

        # 7) Test validation: missing feedback_text (if required)
        invalid_payload_6 = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "rating": 4,
            "service_rating": 5,
        }
        resp_invalid_6 = requests.post(feedback_url, json=invalid_payload_6, headers=headers, timeout=TIMEOUT)
        # Assuming feedback_text is required, expect 400; if optional, expect success
        # We'll assert 400 if feedback_text is required
        assert resp_invalid_6.status_code in (400, 201), "Unexpected status code for missing feedback_text"
        if resp_invalid_6.status_code == 400:
            assert "feedback_text" in resp_invalid_6.text.lower()

    finally:
        # Cleanup: delete created feedback if ID available
        if feedback_id:
            feedback_del_url = f"{feedback_url}{feedback_id}/"
            try:
                requests.delete(feedback_del_url, headers=headers, timeout=TIMEOUT)
            except Exception:
                pass

test_patient_feedback_submission()
