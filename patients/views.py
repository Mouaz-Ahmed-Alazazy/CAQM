"""
Views for the patients app.
Contains patient-specific views like booking appointments, viewing appointments, etc.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.views.generic import CreateView, ListView, View
from django.urls import reverse_lazy
from django.utils import timezone
from django import forms
from datetime import datetime

from appointments.models import Appointment
from accounts.models import Notification
from doctors.models import Doctor
from accounts.notifications import NotificationService
from appointments.services import AppointmentService
from .models import PatientForm
from .services import PatientFormService
from .forms import AppointmentFilterForm
import logging

logger = logging.getLogger(__name__)


class PatientRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only patients can access the view"""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'PATIENT':
            try:
                # Ensure patient profile exists
                _ = request.user.patient_profile
            except:
                from .models import Patient
                Patient.objects.create(user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'PATIENT'

    def handle_no_permission(self):
        messages.error(self.request, 'Only patients can access this page')
        return redirect('accounts:login')


class HomePageView(LoginRequiredMixin, PatientRequiredMixin, ListView):
    """View All Doctors' Availabilities"""
    model = Doctor
    template_name = 'patients/home.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        """Get all doctors"""
        return Doctor.objects.select_related('user').prefetch_related('availability').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctors'] = self.get_queryset()
        return context


class BookAppointmentView(LoginRequiredMixin, PatientRequiredMixin, CreateView):
    """
    Book new appointment.
    """
    model = Appointment
    template_name = 'patients/book_appointment.html'
    success_url = reverse_lazy('patients:my_appointments')
    fields = ['doctor', 'appointment_date', 'start_time', 'notes']

    def get_initial(self):
        """Pre-fill form with query parameters"""
        initial = super().get_initial()
        if 'doctor' in self.request.GET:
            initial['doctor'] = self.request.GET.get('doctor')

        if 'date' in self.request.GET:
            try:
                initial['appointment_date'] = datetime.strptime(
                    self.request.GET.get('date'), '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass

        return initial

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
        form.fields['start_time'].choices = [
            ('', 'Select date and doctor first')]
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

        # Use AppointmentService to book
        success, result = AppointmentService.book_appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_date,
            start_time=start_time,
            notes=notes
        )

        if success:
            self._send_notifications(
                doctor, patient, appointment_date, start_time)
            messages.success(self.request, 'Appointment booked successfully!')
            return redirect(self.success_url)
        else:
            messages.error(self.request, result)
            return self.form_invalid(form)

    def _send_notifications(self, doctor, patient, appointment_date, start_time):
        """Helper to send booking notifications"""
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
            logger.error(f"Failed to send booking notifications: {e}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctors'] = Doctor.objects.all()
        return context


class MyAppointmentsView(LoginRequiredMixin, PatientRequiredMixin, ListView):
    """View patient's appointments with delete functionality"""
    model = Appointment
    template_name = 'patients/my_appointments.html'
    context_object_name = 'upcoming_appointments'
    paginate_by = 10  # Add pagination

    def get_queryset(self):
        """Get only upcoming appointments with related data and filtering"""
        queryset = Appointment.objects.filter(
            patient=self.request.user.patient_profile,
            status__in=['SCHEDULED', 'CHECKED_IN'],
            appointment_date__gte=timezone.now().date()
        ).select_related('doctor__user', 'patient__user')

        # Apply filters
        self.form = AppointmentFilterForm(self.request.GET)
        if self.form.is_valid():
            if self.form.cleaned_data.get('doctor'):
                queryset = queryset.filter(
                    doctor=self.form.cleaned_data['doctor'])
            if self.form.cleaned_data.get('date_from'):
                queryset = queryset.filter(
                    appointment_date__gte=self.form.cleaned_data['date_from'])
            if self.form.cleaned_data.get('date_to'):
                queryset = queryset.filter(
                    appointment_date__lte=self.form.cleaned_data['date_to'])

        return queryset.order_by('appointment_date', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.form

        # Filter past appointments as well if needed, currently just showing last 10
        context['past_appointments'] = Appointment.objects.filter(
            patient=self.request.user.patient_profile,
            status__in=['COMPLETED', 'CANCELLED', 'NO_SHOW']
        ).select_related(
            'doctor__user'  # Prevent N+1 queries
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
                messages.success(
                    request, f'{deleted_count} appointment(s) cancelled successfully')
            else:
                messages.warning(request, 'No appointments were cancelled')

        return redirect('patients:my_appointments')


class ModifyAppointmentView(LoginRequiredMixin, PatientRequiredMixin, View):
    """Modify existing appointment."""
    template_name = 'patients/modify_appointment.html'

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
            return redirect('patients:my_appointments')

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

            new_date = datetime.strptime(
                new_date_str, '%Y-%m-%d').date() if new_date_str else None
            new_time = datetime.strptime(
                new_time_str, '%H:%M').time() if new_time_str else None

            success, result = AppointmentService.modify_appointment(
                pk,
                request.user.patient_profile,
                new_date=new_date,
                new_time=new_time,
                notes=notes
            )

            if success:
                NotificationService.send_booking_confirmation(
                    request.user,
                    result.doctor.user.get_full_name(),
                    result.appointment_date.strftime('%Y-%m-%d'),
                    result.start_time.strftime('%H:%M')
                )
                messages.success(request, 'Appointment modified successfully')
                return redirect('patients:my_appointments')
            else:
                messages.error(request, result)
                return self.render_form(request, appointment)

        except Exception as e:
            messages.error(request, f'Error modifying appointment: {str(e)}')
            return redirect('patients:my_appointments')

    def render_form(self, request, appointment):
        context = {
            'appointment': appointment,
            'doctor': appointment.doctor,
        }
        return render(request, self.template_name, context)


class CancelAppointmentView(LoginRequiredMixin, PatientRequiredMixin, View):
    """Cancel existing appointment."""

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

        return redirect('patients:my_appointments')


class SubmitPatientFormView(LoginRequiredMixin, PatientRequiredMixin, View):
    """Submit medical history form."""
    template_name = 'patients/submit_patient_form.html'

    def get(self, request):
        patient_form = PatientForm.objects.filter(
            patient=request.user.patient_profile).first()
        return render(request, self.template_name, {'patient_form': patient_form})

    def post(self, request):
        try:
            chief_complaint = request.POST.get('chief_complaint', '')
            medical_history = request.POST.get('medical_history', '')
            current_medications = request.POST.get('current_medications', '')
            allergies = request.POST.get('allergies', '')
            symptoms_list = request.POST.getlist('symptoms')
            symptoms = ', '.join(symptoms_list)
            medical_history_list = request.POST.getlist(
                'medical_history_options')
            medical_history_options = ', '.join(medical_history_list)
            allergy_list = request.POST.getlist('allergy_options')
            allergy_options = ', '.join(allergy_list)

            if not chief_complaint and not symptoms:
                messages.error(
                    request, 'Please select at least one symptom or describe your complaint.')
                patient_form = PatientForm.objects.filter(
                    patient=request.user.patient_profile).first()
                return render(request, self.template_name, {'patient_form': patient_form})

            success, result = PatientFormService.submit_form(
                request.user.patient_profile,
                chief_complaint,
                symptoms,
                medical_history,
                current_medications,
                allergies,
                medical_history_options,
                allergy_options
            )

            if success:
                messages.success(
                    request, 'Medical form submitted successfully')
                return redirect('patients:my_appointments')
            else:
                messages.error(request, result)
                patient_form = PatientForm.objects.filter(
                    patient=request.user.patient_profile).first()
                return render(request, self.template_name, {'patient_form': patient_form})

        except Exception as e:
            messages.error(request, f'Error submitting form: {str(e)}')
            patient_form = PatientForm.objects.filter(
                patient=request.user.patient_profile).first()
            return render(request, self.template_name, {'patient_form': patient_form})


class PatientNotificationsView(LoginRequiredMixin, PatientRequiredMixin, ListView):
    template_name = 'patients/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 10

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user, is_read=False
        ).count()
        return context


class MarkNotificationReadView(LoginRequiredMixin, PatientRequiredMixin, View):
    def post(self, request, notification_id):
        Notification.objects.filter(
            pk=notification_id, user=request.user
        ).update(is_read=True)
        return redirect('patients:notifications')


class MarkAllNotificationsReadView(LoginRequiredMixin, PatientRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        messages.success(request, 'All notifications marked as read')
        return redirect('patients:notifications')
