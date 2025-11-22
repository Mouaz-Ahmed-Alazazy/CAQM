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
from .services import AppointmentService, ScheduleService
from accounts.notifications import NotificationService


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
    """
    Book new appointment.
    """
    model = Appointment
    template_name = 'appointments/book_appointment.html'
    success_url = reverse_lazy('appointments:my_appointments')
    fields = ['doctor', 'appointment_date', 'start_time', 'notes']
    
    def get_form(self, form_class=None):
        """Customize the form inline"""
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
        """Handle successful booking"""
        patient = self.request.user.patient_profile
        doctor = form.cleaned_data['doctor']
        appointment_date = form.cleaned_data['appointment_date']
        start_time = form.cleaned_data['start_time']
        notes = form.cleaned_data.get('notes', '')
        
        # Use AppointmentService to book (as per sequence diagram)
        success, result = AppointmentService.book_appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_date,
            start_time=start_time,
            notes=notes
        )
        
        if success:
            appointment = result
            # Send notifications to both patient and doctor.
            try:
                NotificationService.send_booking_confirmation(
                    self.request.user,
                    doctor_name=f"Dr. {doctor.user.get_full_name()}",
                    date=appointment_date.strftime('%Y-%m-%d'),
                    time=start_time.strftime('%I:%M %p')
                )
                NotificationService.send_new_appointment_notification(
                    doctor.user,
                    patient_name=patient.user.get_full_name(),
                    date=appointment_date.strftime('%Y-%m-%d'),
                    time=start_time.strftime('%I:%M %p')
                )
            except Exception as e:
                # Don't block booking if notification fails
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send booking notifications: {e}")
            
            messages.success(self.request, 'Appointment booked successfully!')
            return redirect(self.success_url)
        else:
            messages.error(self.request, result)
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctors'] = Doctor.objects.all()
        return context


class GetAvailableSlotsView(LoginRequiredMixin, View):
    """
    AJAX view to get available slots - returns JSON
    """
    
    def get(self, request, *args, **kwargs):
        doctor_id = request.GET.get('doctor_id')
        date_str = request.GET.get('date')
        
        if not doctor_id or not date_str:
            return JsonResponse({'slots': []})
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            if date < timezone.now().date():
                return JsonResponse({
                    'slots': [],
                    'error': 'Cannot book appointment in the past'
                })
            
            # Use AppointmentService to get available slots
            available_slots = AppointmentService.get_available_slots(doctor_id, date)
            
            # Get slot duration for display formatting
            day_of_week = date.strftime('%A').upper()
            availability = DoctorAvailability.objects.filter(
                doctor_id=doctor_id,
                day_of_week=day_of_week,
                is_active=True
            ).first()
            
            slot_duration = availability.slot_duration if availability else 30
            
            slots_data = []
            for slot in available_slots:
                start_dt = datetime.combine(date, slot)
                end_dt = start_dt + timedelta(minutes=slot_duration)
                display_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
                
                slots_data.append({
                    'time': slot.strftime('%H:%M'),
                    'display': display_str
                })
            
            return JsonResponse({'slots': slots_data})
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
    """
    Doctor dashboard - view appointments and manage availability
    """
    template_name = 'appointments/doctor_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.request.user.doctor_profile
        
        # Get availabilities using ScheduleService
        context['availabilities'] = ScheduleService.get_doctor_schedule(doctor)
        
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


class ModifyAppointmentView(LoginRequiredMixin, PatientRequiredMixin, View):
    """
    Modify existing appointment.
    """
    template_name = 'appointments/modify_appointment.html'
    
    def get(self, request, pk):
        try:
            appointment = get_object_or_404(
                Appointment,
                pk=pk,
                patient=request.user.patient_profile,
                status='SCHEDULED'
            )
            return self.render_form(request, appointment)
        except Exception as e:
            messages.error(request, f'Error loading appointment: {str(e)}')
            return redirect('appointments:my_appointments')
    
    def post(self, request, pk):
        try:
            appointment = get_object_or_404(
                Appointment,
                pk=pk,
                patient=request.user.patient_profile,
                status='SCHEDULED'
            )
            
            new_date_str = request.POST.get('appointment_date')
            new_time_str = request.POST.get('start_time')
            notes = request.POST.get('notes', '')
            
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date() if new_date_str else None
            new_time = datetime.strptime(new_time_str, '%H:%M').time() if new_time_str else None
            
            success, result = AppointmentService.modify_appointment(
                pk,
                request.user.patient_profile,
                new_date=new_date,
                new_time=new_time,
                notes=notes
            )
            
            if success:
                # Send notifications
                NotificationService.send_booking_confirmation(
                    request.user,
                    result.doctor.user.get_full_name(),
                    result.appointment_date.strftime('%Y-%m-%d'),
                    result.start_time.strftime('%H:%M')
                )
                messages.success(request, 'Appointment modified successfully')
                return redirect('appointments:my_appointments')
            else:
                messages.error(request, result)
                return self.render_form(request, appointment)
                
        except Exception as e:
            messages.error(request, f'Error modifying appointment: {str(e)}')
            return redirect('appointments:my_appointments')
    
    def render_form(self, request, appointment):
        from django.shortcuts import render
        context = {
            'appointment': appointment,
            'doctor': appointment.doctor,
        }
        return render(request, self.template_name, context)


class CancelAppointmentView(LoginRequiredMixin, PatientRequiredMixin, View):
    """
    Cancel existing appointment.
    """
    
    def post(self, request, pk):
        try:
            success, message = AppointmentService.cancel_appointment(
                pk,
                request.user.patient_profile
            )
            
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
                
        except Exception as e:
            messages.error(request, f'Error cancelling appointment: {str(e)}')
        
        return redirect('appointments:my_appointments')


class SubmitPatientFormView(LoginRequiredMixin, PatientRequiredMixin, View):
    """
    Submit medical history form.
    """
    template_name = 'appointments/submit_patient_form.html'
    
    def get(self, request):
        from django.shortcuts import render
        return render(request, self.template_name)
    
    def post(self, request):
        from .services import PatientFormService
        
        try:
            chief_complaint = request.POST.get('chief_complaint', '')
            medical_history = request.POST.get('medical_history', '')
            current_medications = request.POST.get('current_medications', '')
            allergies = request.POST.get('allergies', '')
            
            if not chief_complaint:
                messages.error(request, 'Chief complaint is required')
                from django.shortcuts import render
                return render(request, self.template_name)
            
            success, result = PatientFormService.submit_form(
                request.user.patient_profile,
                chief_complaint,
                medical_history,
                current_medications,
                allergies
            )
            
            if success:
                messages.success(request, 'Medical form submitted successfully')
                return redirect('appointments:my_appointments')
            else:
                messages.error(request, result)
                from django.shortcuts import render
                return render(request, self.template_name)
                
        except Exception as e:
            messages.error(request, f'Error submitting form: {str(e)}')
            from django.shortcuts import render
            return render(request, self.template_name)