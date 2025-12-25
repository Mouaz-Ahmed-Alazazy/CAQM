from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
import logging

logger = logging.getLogger(__name__)

class Patient(models.Model):
    """Patient profile extending User"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='patient_profile')
    address = models.TextField(blank=True)
    emergency_regex = RegexValidator(
        regex=r'^(091|092|093|094)\d{7}$',
        message="Emergency contact number must be in the format: '091xxxxxxx', '092xxxxxxx', '093xxxxxxx', or '094xxxxxxx' (10 digits total)."
    )
    emergency_contact = models.CharField(validators=[emergency_regex], max_length=10, blank=True)
    
    class Meta:
        db_table = 'patients'
    
    def __str__(self):
        return self.user.get_full_name()


class PatientForm(models.Model):
    """Patient medical history and information forms"""
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_forms')
    chief_complaint = models.TextField(help_text="Main reason for visit")
    medical_history = models.TextField(blank=True, help_text="Past medical conditions")
    current_medications = models.TextField(blank=True, help_text="Current medications being taken")
    allergies = models.TextField(blank=True, help_text="Known allergies")
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patient_forms'
        ordering = ['-submitted_at']
    
    def __str__(self):
        try:
            return f"Form by {self.patient} - {self.submitted_at.strftime('%Y-%m-%d')}"
        except Exception as e:
            logger.error(f"Error in PatientForm.__str__: {e}")
            return f"PatientForm {self.pk}"
