from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import Patient, Doctor

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
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availability')
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
        return f"{self.doctor} - {self.get_day_of_week_display()}: {self.start_time}-{self.end_time}"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time')


class Appointment(models.Model):
    """Patient appointments with doctors"""
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('CHECKED_IN', 'Checked In'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointments'
        ordering = ['-appointment_date', '-start_time']
        unique_together = ['doctor', 'appointment_date', 'start_time']
    
    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.appointment_date} at {self.start_time}"
    
    def clean(self):
        """Validate appointment rules"""
        if self.appointment_date < timezone.now().date():
            raise ValidationError('Cannot book appointment in the past')
        
        # Check if patient already has appointment with same specialization on same day
        if self.patient_id and self.doctor:
            existing = Appointment.objects.filter(
                patient=self.patient_id,
                appointment_date=self.appointment_date,
                doctor__specialization=self.doctor.specialization,
                status__in=['SCHEDULED', 'CHECKED_IN']
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'You already have an appointment with a {self.doctor.get_specialization_display()} '
                    f'on {self.appointment_date}'
                )
        
        # Check doctor's max appointments per day (15)
        if self.doctor:
            appointments_count = Appointment.objects.filter(    
                doctor=self.doctor,
                appointment_date=self.appointment_date,
                status__in=['SCHEDULED', 'CHECKED_IN']
            ).exclude(pk=self.pk).count()
            
            if appointments_count >= 15:
                raise ValidationError('Doctor has reached maximum appointments for this day')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)