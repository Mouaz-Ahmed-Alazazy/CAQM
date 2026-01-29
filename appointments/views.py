
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta

from doctors.models import DoctorAvailability
from .services import AppointmentService
from .config import SingletonConfig


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
            
            slot_duration = availability.slot_duration if availability else SingletonConfig().default_slot_duration
            
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


class GetDoctorAvailabilityView(LoginRequiredMixin, View):
    """
    AJAX view to get a doctor's weekly availability schedule - returns JSON
    """
    
    # Day ordering for consistent display
    DAY_ORDER = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
    
    def get(self, request, *args, **kwargs):
        doctor_id = request.GET.get('doctor_id')
        
        if not doctor_id:
            return JsonResponse({'schedule': [], 'error': 'Doctor ID is required'})
        
        try:
            from doctors.models import Doctor
            
            # Verify doctor exists
            doctor = Doctor.objects.select_related('user').get(pk=doctor_id)
            
            # Get all active availability for this doctor
            availabilities = DoctorAvailability.objects.filter(
                doctor_id=doctor_id,
                is_active=True
            )
            
            # Build schedule data sorted by day order
            schedule_data = []
            for availability in availabilities:
                schedule_data.append({
                    'day': availability.day_of_week,
                    'day_display': availability.get_day_of_week_display(),
                    'start_time': availability.start_time.strftime('%I:%M %p'),
                    'end_time': availability.end_time.strftime('%I:%M %p'),
                    'slot_duration': availability.slot_duration,
                    'order': self.DAY_ORDER.index(availability.day_of_week)
                })
            
            # Sort by day order
            schedule_data.sort(key=lambda x: x['order'])
            
            # Remove order key from response
            for item in schedule_data:
                del item['order']
            
            return JsonResponse({
                'schedule': schedule_data,
                'doctor_name': f"Dr. {doctor.user.get_full_name()}",
                'specialization': doctor.get_specialization_display(),
                'consultation_fee': str(doctor.consultation_fee)
            })
            
        except Doctor.DoesNotExist:
            return JsonResponse({'schedule': [], 'error': 'Doctor not found'})
        except Exception as e:
            return JsonResponse({'schedule': [], 'error': str(e)})
