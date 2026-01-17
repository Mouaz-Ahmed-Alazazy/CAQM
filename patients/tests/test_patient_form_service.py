"""
Tests for PatientFormService success paths.
Exception handling is already covered in appointments/tests/test_service_exceptions.py
"""
import pytest
from patients.services import PatientFormService
from patients.models import PatientForm


@pytest.mark.django_db
class TestPatientFormServiceSuccessPaths:
    """Test PatientFormService success scenarios"""
    
    def test_submit_form_success_all_fields(self, patient):
        """Test successful form submission with all fields"""
        success, form = PatientFormService.submit_form(
            patient=patient,
            chief_complaint='Severe headache',
            medical_history='History of migraines',
            current_medications='Ibuprofen 400mg',
            allergies='Penicillin'
        )
        
        assert success is True
        assert isinstance(form, PatientForm)
        assert form.patient == patient
        assert form.chief_complaint == 'Severe headache'
        assert form.medical_history == 'History of migraines'
        assert form.current_medications == 'Ibuprofen 400mg'
        assert form.allergies == 'Penicillin'
    
    def test_submit_form_success_required_only(self, patient):
        """Test submission with only required fields"""
        success, form = PatientFormService.submit_form(
            patient=patient,
            chief_complaint='Chest pain'
            # Other fields use default empty strings
        )
        
        assert success is True
        assert isinstance(form, PatientForm)
        assert form.chief_complaint == 'Chest pain'
        assert form.medical_history == ''
        assert form.current_medications == ''
        assert form.allergies == ''
    
    def test_submit_form_creates_database_record(self, patient):
        """Test form is persisted to database"""
        initial_count = PatientForm.objects.filter(patient=patient).count()
        
        success, form = PatientFormService.submit_form(
            patient=patient,
            chief_complaint='Fever and cough',
            medical_history='No significant history'
        )
        
        assert success is True
        
        # Check database
        new_count = PatientForm.objects.filter(patient=patient).count()
        assert new_count == initial_count + 1
        
        # Verify the form exists in database
        db_form = PatientForm.objects.get(pk=form.pk)
        assert db_form.chief_complaint == 'Fever and cough'
    
    def test_submit_form_sets_timestamps(self, patient):
        """Test submitted_at and updated_at are set automatically"""
        success, form = PatientFormService.submit_form(
            patient=patient,
            chief_complaint='Back pain'
        )
        
        assert success is True
        assert form.submitted_at is not None
        assert form.updated_at is not None
    
    def test_get_patient_forms_returns_all_forms(self, patient):
        """Test retrieving all patient forms"""
        # Create multiple forms
        PatientForm.objects.create(
            patient=patient,
            chief_complaint='First complaint'
        )
        PatientForm.objects.create(
            patient=patient,
            chief_complaint='Second complaint'
        )
        PatientForm.objects.create(
            patient=patient,
            chief_complaint='Third complaint'
        )
        
        forms = PatientFormService.get_patient_forms(patient)
        
        assert forms.count() == 3
        complaints = [form.chief_complaint for form in forms]
        assert 'First complaint' in complaints
        assert 'Second complaint' in complaints
        assert 'Third complaint' in complaints
    
    def test_get_patient_forms_ordered_by_date(self, patient):
        """Test forms are ordered by submission date (newest first)"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create forms with different timestamps
        form1 = PatientForm.objects.create(
            patient=patient,
            chief_complaint='Oldest'
        )
        form1.submitted_at = timezone.now() - timedelta(days=2)
        form1.save()
        
        form2 = PatientForm.objects.create(
            patient=patient,
            chief_complaint='Middle'
        )
        form2.submitted_at = timezone.now() - timedelta(days=1)
        form2.save()
        
        form3 = PatientForm.objects.create(
            patient=patient,
            chief_complaint='Newest'
        )
        
        forms = PatientFormService.get_patient_forms(patient)
        
        # Should be ordered newest first (descending)
        complaints = [form.chief_complaint for form in forms]
        assert complaints[0] == 'Newest'
        assert complaints[1] == 'Middle'
        assert complaints[2] == 'Oldest'
    
    def test_get_patient_forms_filters_by_patient(self, patient, db):
        """Test forms are filtered to specific patient only"""
        from accounts.models import User
        
        # Create another patient
        other_user = User.objects.create_user(
            email='other@example.com',
            password='password123',
            first_name='Other',
            last_name='Patient',
            date_of_birth='1985-01-01',
            role='PATIENT',
            phone='0921234567'
        )
        from patients.models import Patient
        other_patient = Patient.objects.create(
            user=other_user,
            address='456 Other St'
        )
        
        # Create forms for both patients
        PatientForm.objects.create(
            patient=patient,
            chief_complaint='My complaint'
        )
        PatientForm.objects.create(
            patient=other_patient,
            chief_complaint='Other complaint'
        )
        
        # Get forms for first patient
        forms = PatientFormService.get_patient_forms(patient)
        
        assert forms.count() == 1
        assert forms.first().chief_complaint == 'My complaint'
    
    def test_get_patient_forms_empty_for_new_patient(self, db):
        """Test empty queryset for patient with no forms"""
        from accounts.models import User
        
        user = User.objects.create_user(
            email='newpatient@example.com',
            password='password123',
            first_name='New',
            last_name='Patient',
            date_of_birth='1995-01-01',
            role='PATIENT',
            phone='0931234567'
        )
        from patients.models import Patient
        new_patient = Patient.objects.create(
            user=user,
            address='789 New St'
        )
        
        forms = PatientFormService.get_patient_forms(new_patient)
        
        assert forms.count() == 0
