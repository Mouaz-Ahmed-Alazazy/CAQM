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

## Admin Dashboard
The admin dashboard (`/admins/`) provides comprehensive queue management:
- **Overview stats**: Doctors, patients, nurses, appointments, queues counts
- **Today's summary**: Waiting, in-progress, completed, emergency queue counts
- **Doctor statistics**: Tabbed view for All Doctors / Past / Today / Future queues
- **Date filtering**: Filter statistics by date range
- **Navigation**: Bidirectional links between custom dashboard and Django admin

### Test Admin Account
- Email: admin@clinic.com
- Password: admin123456

## Recent Changes
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
