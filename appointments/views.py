
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta

from .models import DoctorAvailability
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
