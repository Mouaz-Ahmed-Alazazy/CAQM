"""
Views for the nurses app.
Uses class-based views following the project's existing patterns.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .models import Nurse
from .services import NurseService
from queues.models import PatientQueue
from appointments.models import Appointment


class NurseRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only nurses can access the view"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_nurse()
    
    def handle_no_permission(self):
        messages.error(self.request, 'Only nurses can access this page')
        return redirect('accounts:login')


class NurseDashboardView(LoginRequiredMixin, NurseRequiredMixin, TemplateView):
    """
    Main dashboard for nurses.
    Shows assigned doctor's queue and statistics.
    """
    template_name = 'nurses/nurse_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            nurse = self.request.user.nurse_profile
        except Nurse.DoesNotExist:
            context['error'] = 'Nurse profile not found. Please contact administrator.'
            return context
        
        # Get assigned doctor's queue
        queue = NurseService.get_assigned_doctor_queue(nurse)
        
        context['nurse'] = nurse
        context['queue'] = queue
        context['assigned_doctor'] = nurse.assigned_doctor
        
        if queue:
            context['waiting_patients'] = NurseService.get_waiting_patients(queue)
            context['current_patient'] = NurseService.get_current_patient(queue)
            context['statistics'] = NurseService.get_queue_statistics(queue)
            
            # Get today's appointments for the assigned doctor
            today = timezone.now().date()
            context['today_appointments'] = Appointment.objects.filter(
                doctor=nurse.assigned_doctor,
                appointment_date=today,
                status__in=['SCHEDULED', 'CHECKED_IN', 'IN_PROGRESS']
            ).order_by('start_time')
        
        context['today_date'] = timezone.now().date()
        
        return context


class QueueManagementView(LoginRequiredMixin, NurseRequiredMixin, TemplateView):
    """
    Queue management interface for nurses.
    Allows managing patient queue, calling patients, etc.
    """
    template_name = 'nurses/queue_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            nurse = self.request.user.nurse_profile
        except Nurse.DoesNotExist:
            context['error'] = 'Nurse profile not found'
            return context
        
        queue = NurseService.get_assigned_doctor_queue(nurse)
        
        context['nurse'] = nurse
        context['queue'] = queue
        context['assigned_doctor'] = nurse.assigned_doctor
        
        if queue:
            context['all_patients'] = NurseService.get_queue_patients(queue)
            context['waiting_patients'] = NurseService.get_waiting_patients(queue)
            context['current_patient'] = NurseService.get_current_patient(queue)
            context['statistics'] = NurseService.get_queue_statistics(queue)
        
        context['today_date'] = timezone.now().date()
        
        return context


class CallNextPatientView(LoginRequiredMixin, NurseRequiredMixin, View):
    """
    Call the next patient in the queue.
    """
    
    def post(self, request, *args, **kwargs):
        try:
            nurse = request.user.nurse_profile
            queue = NurseService.get_assigned_doctor_queue(nurse)
            
            success, result = NurseService.call_next_patient(queue)
            
            if success:
                messages.success(
                    request, 
                    f'Called patient: {result.patient.user.get_full_name()}'
                )
            else:
                messages.warning(request, result)
                
        except Nurse.DoesNotExist:
            messages.error(request, 'Nurse profile not found')
        except Exception as e:
            messages.error(request, f'Error calling next patient: {str(e)}')
        
        return redirect('nurses:queue_management')


class StartConsultationView(LoginRequiredMixin, NurseRequiredMixin, View):
    """
    Start consultation for a specific patient.
    """
    
    def post(self, request, pk, *args, **kwargs):
        try:
            success, result = NurseService.start_consultation(pk)
            
            if success:
                messages.success(
                    request, 
                    f'Consultation started for: {result.patient.user.get_full_name()}'
                )
            else:
                messages.error(request, result)
                
        except Exception as e:
            messages.error(request, f'Error starting consultation: {str(e)}')
        
        return redirect('nurses:queue_management')


class EndConsultationView(LoginRequiredMixin, NurseRequiredMixin, View):
    """
    End consultation for a specific patient.
    """
    
    def post(self, request, pk, *args, **kwargs):
        try:
            success, result = NurseService.end_consultation(pk)
            
            if success:
                duration = result.get_consultation_duration()
                messages.success(
                    request, 
                    f'Consultation ended for: {result.patient.user.get_full_name()} '
                    f'(Duration: {duration} minutes)'
                )
            else:
                messages.error(request, result)
                
        except Exception as e:
            messages.error(request, f'Error ending consultation: {str(e)}')
        
        return redirect('nurses:queue_management')


class MarkNoShowView(LoginRequiredMixin, NurseRequiredMixin, View):
    """
    Mark a patient as no-show.
    """
    
    def post(self, request, pk, *args, **kwargs):
        try:
            success, result = NurseService.mark_no_show(pk)
            
            if success:
                messages.success(
                    request, 
                    f'Patient marked as no-show: {result.patient.user.get_full_name()}'
                )
            else:
                messages.error(request, result)
                
        except Exception as e:
            messages.error(request, f'Error marking no-show: {str(e)}')
        
        return redirect('nurses:queue_management')
