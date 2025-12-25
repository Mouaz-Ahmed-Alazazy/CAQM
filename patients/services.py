from patients.models import PatientForm
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class PatientFormService:
    """
    Service layer for patient medical form management.
    """
    
    @staticmethod
    @transaction.atomic
    def submit_form(patient, chief_complaint, medical_history='', current_medications='', allergies=''):
        """
        Submit a patient medical form.
        """
        try:
            form = PatientForm.objects.create(
                patient=patient,
                chief_complaint=chief_complaint,
                medical_history=medical_history,
                current_medications=current_medications,
                allergies=allergies
            )
            logger.info(f"Patient form {form.pk} submitted by patient {patient.pk}")
            return True, form
        except Exception as e:
            logger.error(f"Error submitting patient form: {e}", exc_info=True)
            return False, f'Failed to submit form: {str(e)}'
    
    @staticmethod
    def get_patient_forms(patient):
        """
        Get all forms submitted by a patient.
        """
        try:
            return PatientForm.objects.filter(patient=patient).order_by('-submitted_at')
        except Exception as e:
            logger.error(f"Error getting forms for patient {patient.pk}: {e}")
            return PatientForm.objects.none()
