from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, View, TemplateView
from django.views.generic.edit import FormMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.forms import modelform_factory
from django import forms
from datetime import datetime, timedelta

from .models import Appointment, DoctorAvailability
from accounts.models import Doctor, Patient


class PatientRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only patients can access the view"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_patient()
    
    def handle_no_permission(self):
        messages.error(self.request, 'Only patients can access this page')
        return redirect('accounts:login')


class DoctorRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only doctors can access the view"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_doctor()
    
    def handle_no_permission(self):
        messages.error(self.request, 'Only doctors can access this page')
        return redirect('accounts:login')


class BookAppointmentView(LoginRequiredMixin, PatientRequiredMixin, CreateView):
    """Book new appointment - using inline form definition"""
    model = Appointment
    template_name = 'appointments/book_appointment.html'
    success_url = reverse_lazy('appointments:my_appointments')
    fields = ['doctor', 'appointment_date', 'start_time', 'notes']
    
    def get_form(self, form_class=None):
        """Customize the form inline - no separate forms.py needed"""
        form = super().get_form(form_class)
        
        # Customize doctor field
        form.fields['doctor'].queryset = Doctor.objects.all()
        form.fields['doctor'].label_from_instance = lambda obj: f"Dr. {obj.user.get_full_name()} - {obj.get_specialization_display()}"
        form.fields['doctor'].widget.attrs.update({'class': 'form-control'})
        
        # Customize date field
        form.fields['appointment_date'].widget = forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': timezone.now().date().isoformat()
        })
        
        # Customize time field as select (will be populated via AJAX)
        form.fields['start_time'].widget = forms.Select(attrs={
            'class': 'form-control',
            'id': 'timeSlotSelect'
        })
        form.fields['start_time'].choices = [('', 'Select date and doctor first')]
        form.fields['start_time'].required = True
        
        # Customize notes field
        form.fields['notes'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any specific concerns or notes...'
        })
        form.fields['notes'].required = False
        
        return form
    
    def form_valid(self, form):
        appointment = form.save(commit=False)
        appointment.patient = self.request.user.patient_profile
        
        # Calculate end time based on slot duration
        doctor = appointment.doctor
        day_of_week = appointment.appointment_date.strftime('%A').upper()
        availability = DoctorAvailability.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            is_active=True
        ).first()
        
        if availability:
            start_datetime = datetime.combine(appointment.appointment_date, appointment.start_time)
            end_datetime = start_datetime + timedelta(minutes=availability.slot_duration)
            appointment.end_time = end_datetime.time()
        else:
            messages.error(self.request, 'Doctor is not available on this day')
            return self.form_invalid(form)
        
        try:
            appointment.save()
            messages.success(self.request, 'Appointment booked successfully!')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctors'] = Doctor.objects.all()
        return context


class GetAvailableSlotsView(LoginRequiredMixin, View):
    """AJAX view to get available slots - returns JSON"""
    
    def get(self, request, *args, **kwargs):
        doctor_id = request.GET.get('doctor_id')
        date_str = request.GET.get('date')
        
        if not doctor_id or not date_str:
            return JsonResponse({'slots': []})
        
        try:
            doctor = Doctor.objects.get(pk=doctor_id)
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            if date < timezone.now().date():
                return JsonResponse({
                    'slots': [],
                    'error': 'Cannot book appointment in the past'
                })
            
            available_slots = doctor.get_available_slots_for_date(date)
            slots_data = [
                {
                    'time': slot.strftime('%H:%M'),
                    'display': slot.strftime('%I:%M %p')
                }
                for slot in available_slots
            ]
            
            return JsonResponse({'slots': slots_data})
        except Doctor.DoesNotExist:
            return JsonResponse({'slots': [], 'error': 'Doctor not found'})
        except Exception as e:
            return JsonResponse({'slots': [], 'error': str(e)})


class MyAppointmentsView(LoginRequiredMixin, PatientRequiredMixin, ListView):
    """View patient's appointments with delete functionality"""
    model = Appointment
    template_name = 'appointments/my_appointments.html'
    context_object_name = 'upcoming_appointments'
    
    def get_queryset(self):
        """Get only upcoming appointments"""
        return Appointment.objects.filter(
            patient=self.request.user.patient_profile,
            status__in=['SCHEDULED', 'CHECKED_IN'],
            appointment_date__gte=timezone.now().date()
        ).order_by('appointment_date', 'start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add past appointments
        context['past_appointments'] = Appointment.objects.filter(
            patient=self.request.user.patient_profile,
            status__in=['COMPLETED', 'CANCELLED', 'NO_SHOW']
        ).order_by('-appointment_date', '-start_time')[:10]
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle bulk appointment cancellation"""
        
        appointment_ids = request.POST.getlist('appointment_ids')
        if appointment_ids:
            deleted_count = Appointment.objects.filter(
                id__in=appointment_ids,
                patient=request.user.patient_profile,
                status='SCHEDULED'
            ).update(status='CANCELLED')
            
            if deleted_count > 0:
                messages.success(request, f'{deleted_count} appointment(s) cancelled successfully')
            else:
                messages.warning(request, 'No appointments were cancelled')
        
        return redirect('appointments:my_appointments')


class DoctorDashboardView(LoginRequiredMixin, DoctorRequiredMixin, TemplateView):
    """Doctor dashboard - view appointments and manage availability"""
    template_name = 'appointments/doctor_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor_profile
        
        # Get availabilities
        context['availabilities'] = DoctorAvailability.objects.filter(
            doctor=doctor
        ).order_by('day_of_week')
        
        # Get upcoming appointments
        upcoming = Appointment.objects.filter(
            doctor=doctor,
            status__in=['SCHEDULED', 'CHECKED_IN'],
            appointment_date__gte=timezone.now().date()
        ).order_by('appointment_date', 'start_time')
        
        context['upcoming_appointments'] = upcoming
        context['today_appointments'] = upcoming.filter(
            appointment_date=timezone.now().date()
        )
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
        """Handle availability form submission"""
        if 'availability_form' in request.POST:
            AvailabilityForm = modelform_factory(
                DoctorAvailability,
                fields=['day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active']
            )
            form = AvailabilityForm(request.POST)
            
            if form.is_valid():
                availability = form.save(commit=False)
                availability.doctor = request.user.doctor_profile
                
                try:
                    availability.save()
                    messages.success(request, 'Availability set successfully')
                except Exception as e:
                    messages.error(request, f'Error: {str(e)}')
            else:
                messages.error(request, 'Please correct the errors in the form')
        
        return redirect('appointments:doctor_dashboard')


class DeleteAvailabilityView(LoginRequiredMixin, DoctorRequiredMixin, View):
    """Delete doctor availability"""
    
    def get(self, request, availability_id):
        availability = get_object_or_404(
            DoctorAvailability,
            id=availability_id,
            doctor=request.user.doctor_profile
        )
        availability.delete()
        messages.success(request, 'Availability deleted successfully')
        return redirect('appointments:doctor_dashboard')