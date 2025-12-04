import pytest
from django.test import Client
from accounts.models import User, Patient, Doctor
from appointments.models import DoctorAvailability
from datetime import time

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def patient_user(db):
    user = User.objects.create_user(
        email='patient@example.com',
        password='password123',
        first_name='John',
        last_name='Doe',
        date_of_birth='1990-01-01',
        role='PATIENT',
        phone='0911234567'
    )
    return user

@pytest.fixture
def doctor_user(db):
    user = User.objects.create_user(
        email='doctor@example.com',
        password='password123',
        first_name='Jane',
        last_name='Smith',
        date_of_birth='1980-01-01',
        role='DOCTOR',
        phone='0921234567'
    )
    return user

@pytest.fixture
def patient(patient_user):
    return Patient.objects.create(
        user=patient_user,
        address='123 Main St',
        emergency_contact='0911234567'
    )

@pytest.fixture
def doctor(doctor_user):
    doc = Doctor.objects.create(
        user=doctor_user,
        specialization='CARDIOLOGY',
        license_number='LIC12345',
        bio='Experienced Cardiologist',
        consultation_fee=100.00
    )
    # Create default availability for Monday
    DoctorAvailability.objects.create(
        doctor=doc,
        day_of_week='MONDAY',
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration=30,
        is_active=True
    )
    return doc



@pytest.fixture
def authenticated_patient_client(client, patient_user):
    client.force_login(patient_user)
    return client

@pytest.fixture
def authenticated_doctor_client(client, doctor_user):
    client.force_login(doctor_user)
    return client
