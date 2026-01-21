"""
Views for Queue Check-in functionality.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from appointments.models import Appointment
from .models import PatientQueue
from .services import CheckInService
import json
import logging

logger = logging.getLogger(__name__)


class QRScannerView(LoginRequiredMixin, TemplateView):
    """
    Display QR scanner interface for check-in.
    Mobile-optimized page with camera access.
    """
    template_name = 'queues/qr_scanner.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['user_type'] = 'Doctor' if self.request.user.is_doctor() else 'Patient'
        return context


class ProcessCheckInView(LoginRequiredMixin, View):
    """
    Process check-in after QR code is scanned.
    """
    
    def post(self, request, *args, **kwargs):
        """Handle check-in request"""
        try:
            logger.info(f"Check-in request received from user: {request.user.email}")
            logger.info(f"Request body: {request.body}")
            
            # Parse JSON body
            try:
                data = json.loads(request.body)
                logger.info(f"Parsed JSON data: {data}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid request format.'
                }, status=400)
            
            qr_data = data.get('qr_data', '').strip()
            logger.info(f"QR data extracted: '{qr_data}'")
            
            if not qr_data:
                logger.warning("No QR code data provided")
                return JsonResponse({
                    'success': False,
                    'message': 'No QR code data provided.'
                }, status=400)
            
            # Process check-in through service layer
            logger.info(f"Processing check-in for user {request.user.email} with QR: {qr_data}")
            result = CheckInService.process_check_in(request.user, qr_data)
            logger.info(f"Check-in result: {result}")
            
            # Return JSON response
            status_code = 200 if result['success'] else 400
            return JsonResponse(result, status=status_code)
            
        except Exception as e:
            logger.error(f"Unexpected error in check-in: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'An unexpected error occurred: {str(e)}'
            }, status=500)


class CallNextPatientView(LoginRequiredMixin, View):
    """
    API view for nurses/doctors to call the next patient in the queue.
    """
    def post(self, request, *args, **kwargs):
        queue_id = request.POST.get('queue_id')
        if not queue_id:
            return JsonResponse({'success': False, 'message': 'Queue ID is required.'}, status=400)
            
        success, message, entry = CheckInService.call_next_patient(queue_id)
        return JsonResponse({
            'success': success,
            'message': message,
            'patient_name': str(entry.patient) if entry else None
        })

class QueueStatusAPIView(LoginRequiredMixin, View):
    """
    API view for fetching real-time queue status as JSON.
    """
    def get(self, request, *args, **kwargs):
        patient = request.user.patient_profile
        today = timezone.now().date()
        
        queue_entry = PatientQueue.objects.filter(
            patient=patient,
            queue__date=today,
            status__in=['WAITING', 'IN_PROGRESS']
        ).first()
        
        if not queue_entry:
            return JsonResponse({'has_active_queue': False})
            
        people_ahead = PatientQueue.objects.filter(
            queue=queue_entry.queue,
            status='WAITING',
            position__lt=queue_entry.position
        ).count()
        
        # Recalculate estimated time dynamically
        estimated_time = queue_entry.queue.get_estimated_wait_time(people_ahead + 1)
        
        return JsonResponse({
            'has_active_queue': True,
            'position': queue_entry.position,
            'estimated_time': estimated_time,
            'people_ahead': people_ahead,
            'status': queue_entry.status,
            'doctor_name': str(queue_entry.queue.doctor),
            'last_updated': timezone.now().strftime("%H:%M")
        })

class PatientQueueStatusView(LoginRequiredMixin, TemplateView):
    """
    Display real-time queue status for a patient.
    Shows position, estimated time, and doctor status.
    """
    template_name = 'queues/patient_queue_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.request.user.patient_profile
        
        # Get the patient's active queue entry (WAITING or IN_PROGRESS)
        today = timezone.now().date()
        
        queue_entry = PatientQueue.objects.filter(
            patient=patient,
            queue__date=today,
            status__in=['WAITING', 'IN_PROGRESS']
        ).first()
        
        if not queue_entry:
            context['has_active_queue'] = False
            return context
            
        context['has_active_queue'] = True
        context['queue_entry'] = queue_entry
        context['queue'] = queue_entry.queue
        context['doctor'] = queue_entry.queue.doctor
        
        # Check if doctor has checked in (has any appointments checked in today)
        doctor_checked_in = Appointment.objects.filter(
            doctor=queue_entry.queue.doctor,
            appointment_date=today,
            status__in=['CHECKED_IN', 'IN_PROGRESS', 'COMPLETED']
        ).exists()
        
        context['doctor_checked_in'] = doctor_checked_in
        
        # Calculate dynamic estimated time based on current position
        current_position = queue_entry.position
        # Find how many people are ahead (WAITING with lower position)
        people_ahead = PatientQueue.objects.filter(
            queue=queue_entry.queue,
            status='WAITING',
            position__lt=current_position
        ).count()
        
        context['people_ahead'] = people_ahead
        
        return context