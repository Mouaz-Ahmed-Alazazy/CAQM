from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

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
        from appointments.models import Appointment
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
        

class DoctorAvailability(models.Model):
    """Doctor's working schedule"""
    
    DAY_CHOICES = [
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
        ('FRIDAY', 'Friday'),
        ('SATURDAY', 'Saturday'),
        ('SUNDAY', 'Sunday'),
    ]
    
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField(default=30, help_text="Duration in minutes")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'doctor_availability'
        unique_together = ['doctor', 'day_of_week']
        verbose_name = 'Doctor Availability'
        verbose_name_plural = 'Doctor Availabilities'
    
    def __str__(self):
        try:
            return f"{self.doctor} - {self.get_day_of_week_display()}: {self.start_time}-{self.end_time}"
        except Exception as e:
            logger.error(f"Error in DoctorAvailability.__str__: {e}")
            return f"DoctorAvailability {self.pk}"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time')


