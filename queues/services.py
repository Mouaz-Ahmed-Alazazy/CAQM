"""
Service layer for Queue Check-in business logic.
Handles QR code parsing, appointment verification, and check-in processing.
"""
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime
from appointments.models import Appointment
from patients.models import Patient
from doctors.models import Doctor
from .models import Queue, PatientQueue
import logging

logger = logging.getLogger(__name__)


class CheckInService:
    """Service class for handling patient and doctor check-ins via QR code"""
    
    @staticmethod
    def parse_qr_code(qr_data):
        """
        Parse QR code data to extract doctor_id and date.
        """
        try:
            parts = qr_data.strip().split('-')
            
            if len(parts) != 3 or parts[0] != 'QUEUE':
                logger.error(f"Invalid QR code format: {qr_data}")
                return None, None
            
            doctor_id = int(parts[1])
            date_str = parts[2]
            
            # Parse date from YYYYMMDD format
            date = datetime.strptime(date_str, '%Y%m%d').date()
            
            return doctor_id, date
            
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing QR code '{qr_data}': {e}")
            return None, None
    
    @staticmethod
    def verify_patient_appointment(patient, doctor, date):
        """
        Verify that the patient has a scheduled appointment with the doctor on the given date.
        """
        try:
            appointment = Appointment.objects.get(
                patient=patient,
                doctor=doctor,
                appointment_date=date,
                status='SCHEDULED'
            )
            return appointment
        except Appointment.DoesNotExist:
            logger.warning(f"No scheduled appointment found for patient {patient.pk} with doctor {doctor.pk} on {date}")
            return None
        except Appointment.MultipleObjectsReturned:
            logger.error(f"Multiple appointments found for patient {patient.pk} with doctor {doctor.pk} on {date}")
            return Appointment.objects.filter(
                patient=patient,
                doctor=doctor,
                appointment_date=date,
                status='SCHEDULED'
            ).first()
    
    @staticmethod
    def verify_doctor_consultation(doctor, date):
        """
        Verify that the doctor has scheduled consultations (appointments) on the given date.
        """
        try:
            appointment = Appointment.objects.get(
                patient=patient,
                doctor=doctor,
                appointment_date=date,
                status='SCHEDULED'
            )
            return appointment
            
        except Appointment.DoesNotExist:
            logger.warning(f"No scheduled appointment found for patient {patient.pk} with doctor {doctor.pk} on {date}")
            return None
        except Appointment.MultipleObjectsReturned:
            # Should not happen due to unique_together constraint, but handle it
            logger.error(f"Multiple appointments found for patient {patient.pk} with doctor {doctor.pk} on {date}")
            return Appointment.objects.filter(
                patient=patient,
                doctor=doctor,
                appointment_date=date,
                status='SCHEDULED'
            ).first()
    
    @staticmethod
    def verify_doctor_consultation(doctor, date):
        """
        Verify that the doctor has scheduled consultations (appointments) on the given date.    
        """
        has_consultations = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            status='SCHEDULED'
        ).exists()
        
        if not has_consultations:
            logger.warning(f"Doctor {doctor.pk} has no consultations scheduled for {date}")
        
        return has_consultations
    
    @staticmethod
    def check_in_patient(patient, queue, appointment):
        """
        Check in a patient by adding them to the queue.
        """
        try:
            # Check if patient is already in the queue
            existing_entry = PatientQueue.objects.filter(
                queue=queue,
                patient=patient
            ).first()
            
            if existing_entry:
                return False, "You are already checked in for this appointment.", None
            
            # Create patient queue entry
            patient_queue = PatientQueue.objects.create(
                queue=queue,
                patient=patient,
                status='WAITING',
                checkedin_via_qrcode=True
            )
            
            # Update appointment status to CHECKED_IN
            appointment.status = 'CHECKED_IN'
            appointment.save()
            
            logger.info(f"Patient {patient.pk} checked in to queue {queue.pk} at position {patient_queue.position}")
            
            return True, f"Successfully checked in! Your position in queue: {patient_queue.position}", patient_queue
            
        except Exception as e:
            logger.error(f"Error checking in patient {patient.pk}: {e}")
            return False, "An error occurred during check-in. Please contact reception.", None
    
    @staticmethod
    def check_in_doctor(doctor, queue, date):
        """
        Check in a doctor by updating all their appointments for the day to CHECKED_IN.
        """
        try:
            # Get all scheduled appointments for the doctor on this date
            appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date,
                status='SCHEDULED'
            )
            
            appointments_count = appointments.count()
            
            if appointments_count == 0:
                return False, "No scheduled consultations found for today.", 0
            
            # Update all appointments to CHECKED_IN status
            appointments.update(status='CHECKED_IN')
            
            logger.info(f"Doctor {doctor.pk} checked in for {appointments_count} consultations on {date}")
            
            return True, f"Successfully checked in! You have {appointments_count} consultations today.", appointments_count
            
        except Exception as e:
            logger.error(f"Error checking in doctor {doctor.pk}: {e}")
            return False, "An error occurred during check-in. Please contact reception.", 0
    
    @staticmethod
    def process_check_in(user, qr_data):
        """
        Main entry point for processing check-in from QR code.
        Determines user type (patient/doctor) and calls appropriate method.
        """
        # Parse QR code
        doctor_id, date = CheckInService.parse_qr_code(qr_data)
        
        if not doctor_id or not date:
            return {
                'success': False,
                'message': 'Invalid QR code format.',
                'data': None
            }
        
        # Get the queue
        try:
            doctor = Doctor.objects.get(pk=doctor_id)
            queue, created = Queue.objects.get_or_create(
                doctor=doctor,
                date=date
            )
        except Doctor.DoesNotExist:
            return {
                'success': False,
                'message': 'Invalid QR code: Doctor not found.',
                'data': None
            }
        
        # Check user role and process accordingly
        if user.is_patient():
            # Patient check-in
            patient = user.patient_profile
            appointment = CheckInService.verify_patient_appointment(patient, doctor, date)
            
            if not appointment:
                return {
                    'success': False,
                    'message': f'No scheduled appointment found with {doctor} on {date.strftime("%B %d, %Y")}.',
                    'data': None
                }
            
            success, message, patient_queue = CheckInService.check_in_patient(patient, queue, appointment)
            
            return {
                'success': success,
                'message': message,
                'data': {
                    'position': patient_queue.position if patient_queue else None,
                    'estimated_time': patient_queue.estimated_time if patient_queue else None,
                    'queue_size': queue.get_size()
                }
            }
            
        elif user.is_doctor():
            # Doctor check-in
            doctor_profile = user.doctor_profile
            
            # Verify this is the correct doctor for this QR code
            if doctor_profile.pk != doctor_id:
                return {
                    'success': False,
                    'message': 'This QR code is for a different doctor.',
                    'data': None
                }
            
            has_consultations = CheckInService.verify_doctor_consultation(doctor_profile, date)
            
            if not has_consultations:
                return {
                    'success': False,
                    'message': f'No consultations scheduled for {date.strftime("%B %d, %Y")}.',
                    'data': None
                }
            
            success, message, count = CheckInService.check_in_doctor(doctor_profile, queue, date)
            
            return {
                'success': success,
                'message': message,
                'data': {
                    'consultations_count': count,
                    'queue_size': queue.get_size()
                }
            }
        
        else:
            return {
                'success': False,
                'message': 'Invalid user role.',
                'data': None
            }