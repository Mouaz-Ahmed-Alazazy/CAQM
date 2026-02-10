# Clinic Appointment Queue Management System (CAQM)

## Overview
A Django-based clinic appointment and queue management system that handles patient registration, appointments, doctor scheduling, and queue management.

## Project Architecture
- **Framework**: Django 5.0.14
- **Database**: SQLite (development)
- **Python Version**: 3.12

### Apps Structure
- `accounts/` - User authentication and registration
- `admins/` - Admin user management
- `appointments/` - Appointment scheduling and management
- `doctors/` - Doctor profiles, availability, and dashboards
- `nurses/` - Nurse dashboards and queue management
- `patients/` - Patient registration and appointment booking
- `queues/` - Queue status and QR code scanning

## Running the Application
The Django development server runs on port 5000:
```bash
python manage.py runserver 0.0.0.0:5000
```

## Key Configuration
- `ALLOWED_HOSTS = ["*"]` - Allows all hosts for development
- `CSRF_TRUSTED_ORIGINS` - Configured for Replit domains
- Static files served from `/static/`
- Media files served from `/media/`

## User Roles
- Patients - Can register, book appointments, view queue status
- Doctors - Manage availability, view appointments
- Nurses - Manage patient queues
- Admins - Manage all users

## Google OAuth Authentication
- **Library**: django-allauth 65.14.1
- **Provider**: Google OAuth 2.0
- Both login and patient registration support "Continue with Google"
- Google sign-ups auto-create Patient role and profile
- Users missing required fields (date_of_birth, phone, gender) are redirected to profile completion
- Custom adapters in `accounts/adapters.py` handle social login flow
- Credentials stored as secrets: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- Callback URL: `https://<domain>/accounts/google/login/callback/`
- Google SocialApp is auto-configured via `post_migrate` signal in `accounts/apps.py`
- Management command available: `python manage.py setup_google_oauth`
- Credentials stored in DB SocialApp (not inline in settings) to avoid MultipleObjectsReturned error

## Admin Dashboard
The admin dashboard (`/admins/`) provides comprehensive queue management:
- **Overview stats**: Total users, doctors, patients, nurses, admins, appointments, queues counts
- **Today's summary**: Waiting, in-progress, completed, emergency queue counts
- **Doctor statistics**: Tabbed view for All Doctors / Past / Today / Future queues
- **Date filtering**: Filter statistics by date range
- **Navigation**: Bidirectional links between custom dashboard and Django admin
- **Manage Appointments**: Cancel single or bulk appointments, notify patients with alternative recommendations

### Appointment Management (`/admins/appointments/`)
- Filter appointments by doctor, date range, and status
- Cancel individual appointments with reason
- Bulk cancel all active appointments for a doctor (optionally for a specific date)
- Automatic patient notifications with recommended alternatives:
  - Same doctor on a different day (within 14 days)
  - Different doctor with the same specialization (within 14 days)
- Uses queryset.update() instead of model.save() to bypass date validation for cancellations

### Patient Notifications (`/patients/notifications/`)
- In-app notification system via `Notification` model in `accounts/models.py`
- Notification badge in navbar shows unread count
- Cancellation notifications include recommended alternative appointments with direct booking links
- Mark individual or all notifications as read

### Test Admin Account
- Email: admin@clinic.com
- Password: admin123456

## Recent Changes
- February 10, 2026: Admin appointment management & patient notifications
  - Added Manage Appointments page at `/admins/appointments/`
  - Single appointment cancellation with reason and patient notification
  - Bulk cancel all appointments for a doctor (optionally for a specific date)
  - Notification model (`accounts/models.py`) for in-app notifications
  - Recommendation engine: suggests same doctor other days + same specialization doctors within 14 days
  - Patient notification page with unread badge in navbar
  - Direct booking links from recommended alternatives
  - Manage Appointments button added to admin dashboard Quick Navigation
  - Fixed FK mismatch in appointments table (wrong reference to patients.id instead of patients.user_id)
  - Used queryset.update() for cancellations to bypass Appointment.clean() date validation
- February 09, 2026: Google OAuth authentication & bug fixes
  - Integrated django-allauth for Google login/signup
  - Fixed MultipleObjectsReturned error: moved Google credentials from inline settings to DB SocialApp
  - Added auto-setup via post_migrate signal and management command `setup_google_oauth`
  - Fixed adapter bugs (populate_user crash, wrong adapter paths, settings typos)
  - Made date_of_birth/gender nullable for OAuth compatibility
  - Added profile completion redirect for Google sign-up users (includes gender check)
  - Fixed admin dashboard user counts (now role-based, includes admins)
  - Fixed user list page template bug ('pip' typo in disabled button condition)
  - Fixed missing appointments table in database
- February 04, 2026: Added professional admin dashboard
  - Created AdminDashboardService for queue statistics aggregation
  - Built Bootstrap 5 admin dashboard with tabbed interface
  - Added bidirectional navigation between dashboard and Django admin
  - Updated login redirect for admin users
- January 13, 2026: Configured for Replit environment
  - Added CSRF_TRUSTED_ORIGINS for Replit domains
  - Removed mysqlclient dependency (using SQLite)
  - Added gunicorn for production deployment
  - Configured workflow for port 5000
