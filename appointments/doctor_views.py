"""
Additional views for doctor dashboard pages
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.forms import modelform_factory
from django import forms

from .models import Appointment, DoctorAvailability
from .services import ScheduleService
from queues.models import Queue


class DoctorRequiredMixin:
    """Mixin to ensure only doctors can access the view"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_doctor()


class TodayAppointmentsView(LoginRequiredMixin, TemplateView):
    """
    View today's appointments for the doctor
    """
    template_name = 'appointments/today_appointments.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor_profile
        today = timezone.now().date()
        
        # Get or create Queue for today (this automatically generates QR code)
        queue, created = Queue.objects.get_or_create(
            doctor=doctor,
            date=today
        )
        
        # Get today's appointments
        context['today_appointments'] = Appointment.objects.filter(
            doctor=doctor,
            status__in=['SCHEDULED', 'CHECKED_IN'],
            appointment_date=today
        ).order_by('start_time')
        
        context['doctor'] = doctor
        context['today_date'] = today
        context['queue'] = queue
        
        return context


class UpcomingAppointmentsView(LoginRequiredMixin, TemplateView):
    """
    View upcoming appointments for the doctor
    """
    template_name = 'appointments/upcoming_appointments.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor_profile
        
        # Get upcoming appointments (excluding today)
        context['upcoming_appointments'] = Appointment.objects.filter(
            doctor=doctor,
            status__in=['SCHEDULED', 'CHECKED_IN'],
            appointment_date__gt=timezone.now().date()
        ).order_by('appointment_date', 'start_time')
        
        context['doctor'] = doctor
        
        return context


class AvailabilityManagementView(LoginRequiredMixin, TemplateView):
    """
    Manage doctor availability schedule
    """
    template_name = 'appointments/availability_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor_profile
        
        # Get availabilities using ScheduleService
        context['availabilities'] = ScheduleService.get_doctor_schedule(doctor)
        context['doctor'] = doctor
        
        # Create inline form for availability
        context['form'] = self.get_availability_form()
        
        return context
    
    def get_availability_form(self):
        """Create inline form for doctor availability"""
        AvailabilityForm = modelform_factory(
            DoctorAvailability,
            fields=['day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active'],
            widgets={
                'day_of_week': forms.Select(attrs={'class': 'form-control'}),
                'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
                'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
                'slot_duration': forms.NumberInput(attrs={
                    'class': 'form-control',
                    'min': 15,
                    'max': 120,
                    'step': 15,
                    'value': 30
                }),
                'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'checked': True}),
            }
        )
        return AvailabilityForm()
    
    def post(self, request, *args, **kwargs):
        """
        Handle availability form submission
        """
        if 'availability_form' in request.POST:
            AvailabilityForm = modelform_factory(
                DoctorAvailability,
                fields=['day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active']
            )
            form = AvailabilityForm(request.POST)
            
            if form.is_valid():
                # Use ScheduleService to update schedule
                schedule_data = [{
                    'day_of_week': form.cleaned_data['day_of_week'],
                    'start_time': form.cleaned_data['start_time'],
                    'end_time': form.cleaned_data['end_time'],
                    'slot_duration': form.cleaned_data['slot_duration'],
                    'is_active': form.cleaned_data['is_active']
                }]
                
                success, message = ScheduleService.update_schedule(
                    request.user.doctor_profile,
                    schedule_data
                )
                
                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)
            else:
                messages.error(request, 'Please correct the errors in the form')
        
        return redirect('appointments:availability_management')
