
# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** CAQM
- **Date:** 2026-01-12
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

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/14d42bad-3783-4357-b5a2-b83f83c5dd91/ead86755-6582-474f-a512-8bb399ea9c25
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 doctor_availability_scheduling_limit
- **Test Code:** [TC002_doctor_availability_scheduling_limit.py](./TC002_doctor_availability_scheduling_limit.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 166, in <module>
  File "<string>", line 81, in test_doctor_availability_scheduling_limit
  File "<string>", line 22, in create_doctor
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:9000/api/doctors/

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/14d42bad-3783-4357-b5a2-b83f83c5dd91/812a5e50-ab08-4824-8790-18ae7868889d
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 digital_checkin_qrcode_generation
- **Test Code:** [TC003_digital_checkin_qrcode_generation.py](./TC003_digital_checkin_qrcode_generation.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 125, in <module>
  File "<string>", line 60, in test_digital_checkin_qrcode_generation
  File "<string>", line 16, in create_doctor
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:9000/doctors/

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/14d42bad-3783-4357-b5a2-b83f83c5dd91/5777bfa8-3417-4058-860d-e3f7e23b040a
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 real_time_queue_tracking
- **Test Code:** [TC004_real_time_queue_tracking.py](./TC004_real_time_queue_tracking.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 153, in <module>
  File "<string>", line 77, in test_real_time_queue_tracking
  File "<string>", line 21, in create_doctor
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:9000/api/doctors/

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/14d42bad-3783-4357-b5a2-b83f83c5dd91/b4eea237-bc57-4fe6-883c-0cb85e2b83c0
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 user_authentication_and_role_access
- **Test Code:** [TC005_user_authentication_and_role_access.py](./TC005_user_authentication_and_role_access.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 106, in <module>
  File "<string>", line 31, in test_user_authentication_and_role_access
AssertionError: Login failed for patient with status 404

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/14d42bad-3783-4357-b5a2-b83f83c5dd91/9d070824-1030-43c3-a0a3-320519db2673
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 appointment_modification_and_cancellation
- **Test Code:** [TC006_appointment_modification_and_cancellation.py](./TC006_appointment_modification_and_cancellation.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 119, in <module>
  File "<string>", line 61, in test_appointment_modification_and_cancellation
  File "<string>", line 16, in create_doctor
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:9000/api/doctors/

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/14d42bad-3783-4357-b5a2-b83f83c5dd91/230748ae-614a-4577-b1dd-6ccab37614bb
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 emergency_contact_validation
- **Test Code:** [TC007_emergency_contact_validation.py](./TC007_emergency_contact_validation.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 97, in <module>
  File "<string>", line 49, in test_emergency_contact_validation
AssertionError: Failed to create patient with valid emergency contact. Status: 403, Response: <!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <meta name="robots" content="NONE,NOARCHIVE">
  <title>403 Forbidden</title>
  <style type="text/css">
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
    body { font:small sans-serif; background:#eee; color:#000; }
    body>div { border-bottom:1px solid #ddd; }
    h1 { font-weight:normal; margin-bottom:.4em; }
    h1 span { font-size:60%; color:#666; font-weight:normal; }
    #info { background:#f6f6f6; }
    #info ul { margin: 0.5em 4em; }
    #info p, #summary p { padding-top:10px; }
    #summary { background: #ffc; }
    #explanation { background:#eee; border-bottom: 0px none; }
  </style>
</head>
<body>
<div id="summary">
  <h1>Forbidden <span>(403)</span></h1>
  <p>CSRF verification failed. Request aborted.</p>


  <p>You are seeing this message because this site requires a CSRF cookie when submitting forms. This cookie is required for security reasons, to ensure that your browser is not being hijacked by third parties.</p>
  <p>If you have configured your browser to disable cookies, please re-enable them, at least for this site, or for “same-origin” requests.</p>

</div>

<div id="info">
  <h2>Help</h2>
    
    <p>Reason given for failure:</p>
    <pre>
    CSRF cookie not set.
    </pre>
    

  <p>In general, this can occur when there is a genuine Cross Site Request Forgery, or when
  <a
  href="https://docs.djangoproject.com/en/5.0/ref/csrf/">Django’s
  CSRF mechanism</a> has not been used correctly.  For POST forms, you need to
  ensure:</p>

  <ul>
    <li>Your browser is accepting cookies.</li>

    <li>The view function passes a <code>request</code> to the template’s <a
    href="https://docs.djangoproject.com/en/dev/topics/templates/#django.template.backends.base.Template.render"><code>render</code></a>
    method.</li>

    <li>In the template, there is a <code>{% csrf_token
    %}</code> template tag inside each POST form that
    targets an internal URL.</li>

    <li>If you are not using <code>CsrfViewMiddleware</code>, then you must use
    <code>csrf_protect</code> on any views that use the <code>csrf_token</code>
    template tag, as well as those that accept the POST data.</li>

    <li>The form has a valid CSRF token. After logging in in another browser
    tab or hitting the back button after a login, you may need to reload the
    page with the form, because the token is rotated after a login.</li>
  </ul>

  <p>You’re seeing the help section of this page because you have <code>DEBUG =
  True</code> in your Django settings file. Change that to <code>False</code>,
  and only the initial error message will be displayed.  </p>

  <p>You can customize this page using the CSRF_FAILURE_VIEW setting.</p>
</div>

</body>
</html>


- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/14d42bad-3783-4357-b5a2-b83f83c5dd91/affba054-e430-4489-85c0-3fcac52c20c1
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008 notification_delivery_reliability
- **Test Code:** [TC008_notification_delivery_reliability.py](./TC008_notification_delivery_reliability.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 82, in <module>
  File "<string>", line 46, in test_notification_delivery_reliability
AssertionError: Notification sending failed after 3 attempts.

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/14d42bad-3783-4357-b5a2-b83f83c5dd91/adaec124-c08f-4b89-9172-516acce2e656
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC009 patient_feedback_submission
- **Test Code:** [TC009_patient_feedback_submission.py](./TC009_patient_feedback_submission.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 120, in <module>
  File "<string>", line 29, in test_patient_feedback_submission
AssertionError: Failed to submit feedback: <!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <title>Page not found at /api/patients/feedback/</title>
  <meta name="robots" content="NONE,NOARCHIVE">
  <style type="text/css">
    html * { padding:0; margin:0; }
    body * { padding:10px 20px; }
    body * * { padding:0; }
    body { font:small sans-serif; background:#eee; color:#000; }
    body>div { border-bottom:1px solid #ddd; }
    h1 { font-weight:normal; margin-bottom:.4em; }
    h1 span { font-size:60%; color:#666; font-weight:normal; }
    table { border:none; border-collapse: collapse; width:100%; }
    td, th { vertical-align:top; padding:2px 3px; }
    th { width:12em; text-align:right; color:#666; padding-right:.5em; }
    #info { background:#f6f6f6; }
    #info ol { margin: 0.5em 4em; }
    #info ol li { font-family: monospace; }
    #summary { background: #ffc; }
    #explanation { background:#eee; border-bottom: 0px none; }
    pre.exception_value { font-family: sans-serif; color: #575757; font-size: 1.5em; margin: 10px 0 10px 0; }
  </style>
</head>
<body>
  <div id="summary">
    <h1>Page not found <span>(404)</span></h1>
    
    <table class="meta">
      <tr>
        <th>Request Method:</th>
        <td>POST</td>
      </tr>
      <tr>
        <th>Request URL:</th>
        <td>http://localhost:9000/api/patients/feedback/</td>
      </tr>
      
    </table>
  </div>
  <div id="info">
    
      <p>
      Using the URLconf defined in <code>caqm_project.urls</code>,
      Django tried these URL patterns, in this order:
      </p>
      <ol>
        
          <li>
            
                admin/
                
            
          </li>
        
          <li>
            
                accounts/
                
            
          </li>
        
          <li>
            
                admins/
                
            
          </li>
        
          <li>
            
                appointments/
                
            
          </li>
        
          <li>
            
                patients/
                
            
          </li>
        
          <li>
            
                doctors/
                
            
          </li>
        
          <li>
            
                queues/
                
            
          </li>
        
          <li>
            
                nurses/
                
            
          </li>
        
          <li>
            
                
                
            
          </li>
        
          <li>
            
                ^static/(?P&lt;path&gt;.*)$
                
            
          </li>
        
          <li>
            
                ^media/(?P&lt;path&gt;.*)$
                
            
          </li>
        
      </ol>
      <p>
        
          The current path, <code>api/patients/feedback/</code>,
        
        didn’t match any of these.
      </p>
    
  </div>

  <div id="explanation">
    <p>
      You’re seeing this error because you have <code>DEBUG = True</code> in
      your Django settings file. Change that to <code>False</code>, and Django
      will display a standard 404 page.
    </p>
  </div>
</body>
</html>


- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/14d42bad-3783-4357-b5a2-b83f83c5dd91/08237661-b8ed-4032-bec1-e0fdb76aa528
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC010 admin_announcement_broadcast
- **Test Code:** [TC010_admin_announcement_broadcast.py](./TC010_admin_announcement_broadcast.py)
- **Test Error:** Traceback (most recent call last):
  File "<string>", line 22, in get_admin_token
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:9000/api/token/

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 113, in <module>
  File "<string>", line 77, in test_admin_announcement_broadcast
  File "<string>", line 24, in get_admin_token
AssertionError: Failed to authenticate admin user: 404 Client Error: Not Found for url: http://localhost:9000/api/token/

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/14d42bad-3783-4357-b5a2-b83f83c5dd91/2a402d9f-e324-4c48-ba20-e1bc6f6891a2
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