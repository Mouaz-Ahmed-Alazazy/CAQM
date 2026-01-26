from django.utils import timezone
from django.db import transaction
from queues.models import Queue, PatientQueue
from appointments.models import Appointment
import logging

logger = logging.getLogger(__name__)


class NurseService:
    """
    Service class for nurse-related operations.
    Handles queue management and consultation tracking.
    """
    
    @staticmethod
    def get_assigned_doctor_queue(nurse):
        """
        Get the current day's queue for the nurse's assigned doctor.
        """
        if not nurse.assigned_doctor:
            return None
        
        today = timezone.now().date()
        queue, created = Queue.objects.get_or_create(
            doctor=nurse.assigned_doctor,
            date=today
        )
        return queue
    
    @staticmethod
    def get_queue_patients(queue):
        """
        Get all patients in a queue, sorted by position.
        """
        if not queue:
            return PatientQueue.objects.none()
        
        return queue.patient_queues.all().order_by('position')
    
    @staticmethod
    def get_waiting_patients(queue):
        """
        Get patients currently waiting in the queue.
        """
        if not queue:
            return PatientQueue.objects.none()
        
        return queue.patient_queues.filter(status='WAITING').order_by('position')
    
    @staticmethod
    def get_current_patient(queue):
        """
        Get the patient currently in consultation.
        """
        if not queue:
            return None
        
        return queue.patient_queues.filter(status='IN_PROGRESS').first()
    
    @staticmethod
    @transaction.atomic
    def call_next_patient(queue):
        """
        Call the next patient from the queue to start consultation.
        Requires doctor to have checked in first.
        """
        if not queue:
            return False, "No queue available"
        
        # GUARD: Check if doctor has checked in
        from queues.services import CheckInService
        if not CheckInService.is_doctor_checked_in(queue.doctor, queue.date):
            return False, "Doctor hasn't checked in yet."
        
        # Check if there's already a patient in progress
        current = NurseService.get_current_patient(queue)
        if current:
            return False, f"Please complete consultation with {current.patient} first"
        
        # Get next waiting patient
        next_patient = queue.patient_queues.filter(
            status='WAITING'
        ).order_by('position').first()
        
        if not next_patient:
            return False, "No patients waiting in queue"
        
        # Update status
        next_patient.status = 'IN_PROGRESS'
        next_patient.consultation_start_time = timezone.now()
        next_patient.save()
        
        logger.info(f"Called next patient: {next_patient.patient}")
        return True, next_patient
    
    @staticmethod
    @transaction.atomic
    def start_consultation(patient_queue_id):
        """
        Start consultation for a specific patient.
        Requires doctor to have checked in first.
        """
        try:
            patient_queue = PatientQueue.objects.get(pk=patient_queue_id)
            
            # GUARD: Check if doctor has checked in
            from queues.services import CheckInService
            if not CheckInService.is_doctor_checked_in(patient_queue.queue.doctor, patient_queue.queue.date):
                return False, "Doctor hasn't checked in yet."
            
            if patient_queue.status != 'WAITING':
                return False, "Patient is not in waiting status"
            
            patient_queue.status = 'IN_PROGRESS'
            patient_queue.consultation_start_time = timezone.now()
            patient_queue.save()
            
            # Update appointment status if exists
            today = timezone.now().date()
            appointment = Appointment.objects.filter(
                patient=patient_queue.patient,
                doctor=patient_queue.queue.doctor,
                appointment_date=today,
                status='CHECKED_IN'
            ).first()
            
            if appointment:
                appointment.status = 'IN_PROGRESS'
                appointment.save()
            
            logger.info(f"Started consultation for patient: {patient_queue.patient}")
            return True, patient_queue
            
        except PatientQueue.DoesNotExist:
            return False, "Patient queue entry not found"
        except Exception as e:
            logger.error(f"Error starting consultation: {e}")
            return False, str(e)
    
    @staticmethod
    @transaction.atomic
    def end_consultation(patient_queue_id):
        """
        End consultation for a specific patient.
        """
        try:
            patient_queue = PatientQueue.objects.get(pk=patient_queue_id)
            
            if patient_queue.status != 'IN_PROGRESS':
                return False, "Patient is not in consultation"
            
            patient_queue.status = 'TERMINATED'
            patient_queue.consultation_end_time = timezone.now()
            patient_queue.save()
            
            # Update appointment status if exists
            today = timezone.now().date()
            appointment = Appointment.objects.filter(
                patient=patient_queue.patient,
                doctor=patient_queue.queue.doctor,
                appointment_date=today,
                status='IN_PROGRESS'
            ).first()
            
            if appointment:
                appointment.status = 'COMPLETED'
                appointment.save()
            
            logger.info(f"Ended consultation for patient: {patient_queue.patient}")
            return True, patient_queue
            
        except PatientQueue.DoesNotExist:
            return False, "Patient queue entry not found"
        except Exception as e:
            logger.error(f"Error ending consultation: {e}")
            return False, str(e)
    
    @staticmethod
    @transaction.atomic
    def mark_no_show(patient_queue_id):
        """
        Mark a patient as no-show.
        """
        try:
            patient_queue = PatientQueue.objects.get(pk=patient_queue_id)
            
            if patient_queue.status not in ['WAITING', 'EMERGENCY']:
                return False, "Can only mark waiting patients as no-show"
            
            patient_queue.status = 'NO_SHOW'
            patient_queue.save()
            
            # Update appointment status if exists
            today = timezone.now().date()
            appointment = Appointment.objects.filter(
                patient=patient_queue.patient,
                doctor=patient_queue.queue.doctor,
                appointment_date=today,
                status__in=['SCHEDULED', 'CHECKED_IN']
            ).first()
            
            if appointment:
                appointment.status = 'NO_SHOW'
                appointment.save()
            
            logger.info(f"Marked patient as no-show: {patient_queue.patient}")
            return True, patient_queue
            
        except PatientQueue.DoesNotExist:
            return False, "Patient queue entry not found"
        except Exception as e:
            logger.error(f"Error marking no-show: {e}")
            return False, str(e)
    
    @staticmethod
    def get_queue_statistics(queue):
        """
        Get statistics for a queue.
        """
        if not queue:
            return {
                'total': 0,
                'waiting': 0,
                'in_progress': 0,
                'completed': 0,
                'no_show': 0,
            }
        
        patients = queue.patient_queues.all()
        
        return {
            'total': patients.count(),
            'waiting': patients.filter(status='WAITING').count(),
            'in_progress': patients.filter(status='IN_PROGRESS').count(),
            'completed': patients.filter(status='TERMINATED').count(),
            'no_show': patients.filter(status='NO_SHOW').count(),
        }
