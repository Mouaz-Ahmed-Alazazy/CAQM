from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.contrib import messages
from .models import Queue, PatientQueue
from accounts.models import Nurse

class NurseRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.role == 'NURSE' or self.request.user.is_superuser)

class NurseDashboardView(LoginRequiredMixin, NurseRequiredMixin, TemplateView):
    template_name = 'queues/nurse_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the nurse profile
        try:
            nurse = self.request.user.nurse_profile
            doctor = nurse.assigned_doctor
        except:
            # Fallback for testing or if not set up correctly
            doctor = None
            # If superuser or no profile, maybe show all queues or a selector?
            # For now, let's try to find a queue if doctor is None but user is admin
            if self.request.user.is_superuser:
                # Just pick the first active queue for demo
                queue = Queue.objects.filter(date=timezone.now().date()).first()
            else:
                queue = None

        if doctor:
            queue = Queue.objects.filter(doctor=doctor, date=timezone.now().date()).first()
        elif not queue and not doctor:
             # Try to find any queue for today if no specific doctor assigned (or maybe nurse selects?)
             # For simplicity, let's just get the first one
             queue = Queue.objects.filter(date=timezone.now().date()).first()

        context['queue'] = queue
        
        if queue:
            # Logic to find "Current Patient"
            # 1. Is there a patient IN_PROGRESS?
            current_patient = PatientQueue.objects.filter(queue=queue, status='IN_PROGRESS').first()
            
            # 2. If not, who is next WAITING?
            if not current_patient:
                current_patient = PatientQueue.objects.filter(queue=queue, status='WAITING').order_by('position').first()
            
            context['current_patient'] = current_patient
            
            # Waiting list (excluding the one we just picked as current if they are waiting)
            waiting_patients = PatientQueue.objects.filter(queue=queue, status='WAITING').order_by('position')
            if current_patient and current_patient.status == 'WAITING':
                waiting_patients = waiting_patients.exclude(pk=current_patient.pk)
                
            context['waiting_patients'] = waiting_patients
            
        return context

class StartConsultationView(LoginRequiredMixin, NurseRequiredMixin, View):
    def post(self, request, pk):
        patient_queue = get_object_or_404(PatientQueue, pk=pk)
        
        # Validation
        if patient_queue.status != 'WAITING':
            messages.error(request, "Patient is not waiting.")
            return redirect('nurse_dashboard')
            
        # Update status
        patient_queue.status = 'IN_PROGRESS'
        patient_queue.consultation_start_time = timezone.now()
        patient_queue.save()
        
        messages.success(request, f"Consultation started for {patient_queue.patient.user.get_full_name()}")
        return redirect('nurse_dashboard')

class EndConsultationView(LoginRequiredMixin, NurseRequiredMixin, View):
    def post(self, request, pk):
        patient_queue = get_object_or_404(PatientQueue, pk=pk)
        
        # Validation
        if patient_queue.status != 'IN_PROGRESS':
            messages.error(request, "Consultation is not in progress.")
            return redirect('nurse_dashboard')
            
        # Update status
        patient_queue.status = 'TERMINATED'
        patient_queue.consultation_end_time = timezone.now()
        patient_queue.save()
        
        # Notify next patient (Mock)
        # In a real app, this would send SMS/Email or update a websocket
        messages.info(request, "Next patient notified.")
        
        messages.success(request, f"Consultation ended for {patient_queue.patient.user.get_full_name()}")
        return redirect('nurse_dashboard')
