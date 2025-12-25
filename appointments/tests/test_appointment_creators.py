from django.test import TestCase
from django.utils import timezone
from datetime import datetime, time, date
from appointments.models import Appointment, DoctorAvailability
from appointments.appointment_creators import ScheduledAppointmentCreator, WalkInAppointmentCreator
from patients.models import Patient
from doctors.models import Doctor
from accounts.models import User

class AppointmentCreatorTestCase(TestCase):
    def setUp(self):
        # Create Patient User
        self.patient_user = User.objects.create_user(
            email='patient@example.com', 
            password='password123', 
            role='PATIENT',
            first_name='John',
            last_name='Doe',
            date_of_birth=date(1990, 1, 1)
        )
        # Create Patient Profile
        self.patient = Patient.objects.create(
            user=self.patient_user
        )
        
        # Create Doctor User
        self.doctor_user = User.objects.create_user(
            email='doctor@example.com', 
            password='password123', 
            role='DOCTOR',
            first_name='Dr',
            last_name='Smith',
            date_of_birth=date(1980, 1, 1)
        )
        # Create Doctor Profile
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='GENERAL',
            license_number='DOC123'
        )
        
        # Create availability for validation
        self.appointment_date = timezone.now().date()
        # Ensure it's a weekday for simplicity or fetch dynamic day
        self.day_of_week = self.appointment_date.strftime('%A').upper()
        
        DoctorAvailability.objects.create(
            doctor=self.doctor,
            day_of_week=self.day_of_week,
            start_time=time(9, 0),
            end_time=time(17, 0),
            slot_duration=30,
            is_active=True
        )

    def test_scheduled_appointment_creator(self):
        creator = ScheduledAppointmentCreator()
        appointment = creator.create_product(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            start_time=time(10, 0),
            notes="Regular checkup"
        )
        
        # Verify fields
        self.assertEqual(appointment.status, 'SCHEDULED')
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.doctor, self.doctor)
        self.assertEqual(appointment.start_time, time(10, 0))
        self.assertEqual(appointment.end_time, time(10, 30)) # 30 min duration
        self.assertEqual(appointment.notes, "Regular checkup")

    def test_walk_in_appointment_creator(self):
        creator = WalkInAppointmentCreator()
        appointment = creator.create_product(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            start_time=time(11, 0),
            notes="Emergency pain"
        )
        
        # Verify fields specific to Walk-In
        self.assertEqual(appointment.status, 'CHECKED_IN')
        self.assertEqual(appointment.start_time, time(11, 0))
        self.assertEqual(appointment.end_time, time(11, 30))
        self.assertIn("Walk-in appointment", appointment.notes)
        self.assertIn("Emergency pain", appointment.notes)

    def test_admin_appointment_creator(self):
        from appointments.appointment_creators import AdminAppointmentCreator
        creator = AdminAppointmentCreator()
        appointment = creator.create_product(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            start_time=time(14, 0),
            notes="Manual entry"
        )
        
        # Verify fields specific to Admin
        self.assertEqual(appointment.status, 'SCHEDULED')
        self.assertEqual(appointment.start_time, time(14, 0))
        self.assertIn("[ADMIN]", appointment.notes)
        self.assertIn("Manual entry", appointment.notes)

    def test_creator_raises_error_when_doctor_unavailable(self):
        
        DoctorAvailability.objects.all().delete()
        
        creator = ScheduledAppointmentCreator()
        with self.assertRaises(ValueError):
            creator.create_product(
                patient=self.patient,
                doctor=self.doctor,
                appointment_date=self.appointment_date,
                start_time=time(10, 0)
            )
