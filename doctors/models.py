from django.db import models
from django.conf import settings

class Doctor(models.Model):
    """Doctor profile extending User"""
    
    SPECIALIZATION_CHOICES = [
        ('CARDIOLOGY', 'Cardiology'),
        ('DERMATOLOGY', 'Dermatology'),
        ('NEUROLOGY', 'Neurology'),
        ('ORTHOPEDICS', 'Orthopedics'),
        ('PEDIATRICS', 'Pediatrics'),
        ('PSYCHIATRY', 'Psychiatry'),
        ('GENERAL', 'General Medicine'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='doctor_profile')
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES)
    license_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    bio = models.TextField(blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        db_table = 'doctors'
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.get_specialization_display()}"
    
    def get_available_slots_for_date(self, date):
        """Get available time slots for a specific date"""
        from appointments.models import DoctorAvailability, Appointment
        from datetime import datetime, timedelta
        
        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = date.strftime('%A').upper()
        
        # Get doctor's availability for this day
        availability = DoctorAvailability.objects.filter(
            doctor=self,
            day_of_week=day_of_week,
            is_active=True
        ).first()
        
        if not availability:
            return []
        
        # Generate time slots
        slots = []
        start_time = datetime.combine(date, availability.start_time)
        end_time = datetime.combine(date, availability.end_time)
        slot_duration = timedelta(minutes=availability.slot_duration)
        
        current_time = start_time
        while current_time + slot_duration <= end_time:
            slots.append(current_time.time())
            current_time += slot_duration
        
        # Get already booked appointments
        booked_appointments = Appointment.objects.filter(
            doctor=self,
            appointment_date=date,
            status__in=['SCHEDULED', 'CHECKED_IN']
        ).values_list('start_time', flat=True)
        
        # Filter out booked slots
        available_slots = [slot for slot in slots if slot not in booked_appointments]
        
        # Check max appointments per day (15)
        appointments_count = Appointment.objects.filter(
            doctor=self,
            appointment_date=date,
            status__in=['SCHEDULED', 'CHECKED_IN']
        ).count()
        
        if appointments_count >= 15:
            return []
        
        return available_slots[:15 - appointments_count]


