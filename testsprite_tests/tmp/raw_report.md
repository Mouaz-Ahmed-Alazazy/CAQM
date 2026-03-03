
# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** CAQM
- **Date:** 2026-03-03
- **Prepared by:** TestSprite AI Team

---

## 2️⃣ Requirement Validation Summary

#### Test TC001 patient_appointment_booking_validation
- **Test Code:** [TC001_patient_appointment_booking_validation.py](./TC001_patient_appointment_booking_validation.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 3, in <module>
ModuleNotFoundError: No module named 'pytest'

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/77066c21-191f-4750-bc86-aa4bba542f2b/7544fd57-3a87-41a9-aef5-f7f5f74937c8
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 doctor_availability_scheduling_limit
- **Test Code:** [TC002_doctor_availability_scheduling_limit.py](./TC002_doctor_availability_scheduling_limit.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 145, in <module>
  File "<string>", line 57, in test_doctor_availability_scheduling_limit
  File "<string>", line 11, in create_doctor
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:9000/api/doctors/

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/77066c21-191f-4750-bc86-aa4bba542f2b/cbb8d1dc-3129-403b-be26-28bfea2c61f8
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 digital_checkin_qrcode_generation
- **Test Code:** [TC003_digital_checkin_qrcode_generation.py](./TC003_digital_checkin_qrcode_generation.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 149, in <module>
  File "<string>", line 97, in test_digital_checkin_qrcode_generation
  File "<string>", line 14, in authenticate
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:9000/api/auth/login/

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/77066c21-191f-4750-bc86-aa4bba542f2b/6759a653-e1a9-47f1-abfa-99385dd17e3a
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 real_time_queue_tracking
- **Test Code:** [TC004_real_time_queue_tracking.py](./TC004_real_time_queue_tracking.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 184, in <module>
  File "<string>", line 74, in test_real_time_queue_tracking
  File "<string>", line 20, in create_doctor
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:9000/api/doctors/

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/77066c21-191f-4750-bc86-aa4bba542f2b/1320b1ee-b327-451b-be0c-6ac9bb097ccd
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 user_authentication_and_role_access
- **Test Code:** [TC005_user_authentication_and_role_access.py](./TC005_user_authentication_and_role_access.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'pytest'

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/77066c21-191f-4750-bc86-aa4bba542f2b/f95847e7-f1bb-4918-b92f-49c9968c8961
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 appointment_modification_and_cancellation
- **Test Code:** [TC006_appointment_modification_and_cancellation.py](./TC006_appointment_modification_and_cancellation.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 168, in <module>
  File "<string>", line 78, in test_appointment_modification_and_cancellation
  File "<string>", line 14, in create_patient
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: http://localhost:9000/patients/

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/77066c21-191f-4750-bc86-aa4bba542f2b/3b54313e-641a-4b51-8ab4-5171e10ae341
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 emergency_contact_validation
- **Test Code:** [TC007_emergency_contact_validation.py](./TC007_emergency_contact_validation.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 171, in <module>
  File "<string>", line 76, in test_emergency_contact_validation
AssertionError: Expected 201 Created for valid contact 0911234567, got 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/77066c21-191f-4750-bc86-aa4bba542f2b/966a5e88-147a-4f65-ab3c-d7e6695082ba
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008 notification_delivery_reliability
- **Test Code:** [TC008_notification_delivery_reliability.py](./TC008_notification_delivery_reliability.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 93, in <module>
  File "<string>", line 65, in test_notification_delivery_reliability
  File "<string>", line 33, in create_test_patient
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:9000/api/patients/

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/77066c21-191f-4750-bc86-aa4bba542f2b/050c50fc-d300-4589-934d-eb008b130cf6
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC009 patient_feedback_submission
- **Test Code:** [TC009_patient_feedback_submission.py](./TC009_patient_feedback_submission.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'pytest'

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/77066c21-191f-4750-bc86-aa4bba542f2b/f86fb2ba-d022-40a1-9bec-c7cedd400c55
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC010 admin_announcement_broadcast
- **Test Code:** [TC010_admin_announcement_broadcast.py](./TC010_admin_announcement_broadcast.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 81, in <module>
  File "<string>", line 35, in test_admin_announcement_broadcast
AssertionError: Expected 201 Created, got 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/77066c21-191f-4750-bc86-aa4bba542f2b/65ba078e-769e-4c41-96f0-3010fd961325
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **0.00** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---