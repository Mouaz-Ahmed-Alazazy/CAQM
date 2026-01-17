"""
Tests for Patient model validations and methods.
"""
import pytest
from django.core.exceptions import ValidationError
from patients.models import Patient
from accounts.models import User


@pytest.mark.django_db
class TestPatientModel:
    """Test Patient model validations"""
    
    def test_emergency_contact_valid_091_prefix(self, db):
        """Test valid emergency contact with 091 prefix"""
        user = User.objects.create_user(
            email='patient091@example.com',
            password='password123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            role='PATIENT',
            phone='0911234567'
        )
        
        # Should not raise validation error
        patient = Patient(
            user=user,
            address='123 Main St',
            emergency_contact='0911234567'
        )
        patient.full_clean()  # Validates all fields
        patient.save()
        
        assert patient.emergency_contact == '0911234567'
    
    def test_emergency_contact_valid_092_prefix(self, db):
        """Test valid emergency contact with 092 prefix"""
        user = User.objects.create_user(
            email='patient092@example.com',
            password='password123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            role='PATIENT',
            phone='0921234567'
        )
        
        patient = Patient(
            user=user,
            address='123 Main St',
            emergency_contact='0927654321'
        )
        patient.full_clean()
        patient.save()
        
        assert patient.emergency_contact == '0927654321'
    
    def test_emergency_contact_valid_093_prefix(self, db):
        """Test valid emergency contact with 093 prefix"""
        user = User.objects.create_user(
            email='patient093@example.com',
            password='password123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            role='PATIENT',
            phone='0931234567'
        )
        
        patient = Patient(
            user=user,
            address='123 Main St',
            emergency_contact='0931112233'
        )
        patient.full_clean()
        patient.save()
        
        assert patient.emergency_contact == '0931112233'
    
    def test_emergency_contact_valid_094_prefix(self, db):
        """Test valid emergency contact with 094 prefix"""
        user = User.objects.create_user(
            email='patient094@example.com',
            password='password123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            role='PATIENT',
            phone='0941234567'
        )
        
        patient = Patient(
            user=user,
            address='123 Main St',
            emergency_contact='0949876543'
        )
        patient.full_clean()
        patient.save()
        
        assert patient.emergency_contact == '0949876543'
    
    def test_emergency_contact_invalid_prefix(self, db):
        """Test invalid prefix (e.g., 095) raises validation error"""
        user = User.objects.create_user(
            email='patient095@example.com',
            password='password123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            role='PATIENT',
            phone='0951234567'
        )
        
        patient = Patient(
            user=user,
            address='123 Main St',
            emergency_contact='0951234567'  # Invalid prefix
        )
        
        with pytest.raises(ValidationError) as exc_info:
            patient.full_clean()
        
        # Check that the error is about emergency contact
        assert 'emergency_contact' in exc_info.value.error_dict
    
    def test_emergency_contact_invalid_length_too_short(self, db):
        """Test too short number raises validation error"""
        user = User.objects.create_user(
            email='patientshort@example.com',
            password='password123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            role='PATIENT',
            phone='0911234567'
        )
        
        patient = Patient(
            user=user,
            address='123 Main St',
            emergency_contact='091123456'  # Only 9 digits
        )
        
        with pytest.raises(ValidationError) as exc_info:
            patient.full_clean()
        
        assert 'emergency_contact' in exc_info.value.error_dict
    
    def test_emergency_contact_invalid_length_too_long(self, db):
        """Test too long number raises validation error"""
        user = User.objects.create_user(
            email='patientlong@example.com',
            password='password123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            role='PATIENT',
            phone='0911234567'
        )
        
        patient = Patient(
            user=user,
            address='123 Main St',
            emergency_contact='09112345678'  # 11 digits
        )
        
        with pytest.raises(ValidationError) as exc_info:
            patient.full_clean()
        
        assert 'emergency_contact' in exc_info.value.error_dict
    
    def test_emergency_contact_invalid_format_letters(self, db):
        """Test non-numeric characters raise validation error"""
        user = User.objects.create_user(
            email='patientletters@example.com',
            password='password123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            role='PATIENT',
            phone='0911234567'
        )
        
        patient = Patient(
            user=user,
            address='123 Main St',
            emergency_contact='091ABC4567'  # Contains letters
        )
        
        with pytest.raises(ValidationError) as exc_info:
            patient.full_clean()
        
        assert 'emergency_contact' in exc_info.value.error_dict
    
    def test_emergency_contact_can_be_blank(self, db):
        """Test emergency contact is optional (can be blank)"""
        user = User.objects.create_user(
            email='patientblank@example.com',
            password='password123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            role='PATIENT',
            phone='0911234567'
        )
        
        patient = Patient(
            user=user,
            address='123 Main St',
            emergency_contact=''  # Blank
        )
        patient.full_clean()
        patient.save()
        
        assert patient.emergency_contact == ''
    
    def test_patient_str_method(self, patient):
        """Test string representation of Patient"""
        expected = patient.user.get_full_name()
        assert str(patient) == expected
    
    def test_patient_address_can_be_blank(self, db):
        """Test address field is optional"""
        user = User.objects.create_user(
            email='patientnoaddr@example.com',
            password='password123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            role='PATIENT',
            phone='0911234567'
        )
        
        patient = Patient(
            user=user,
            address='',  # Blank address
            emergency_contact='0911234567'
        )
        patient.full_clean()
        patient.save()
        
        assert patient.address == ''
