from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)




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
    
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='appointments')
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
        indexes = [
            models.Index(fields=['appointment_date', 'status'], name='appt_date_status_idx'),
            models.Index(fields=['doctor', 'appointment_date'], name='appt_doctor_date_idx'),
            models.Index(fields=['patient', 'appointment_date'], name='appt_patient_date_idx'),
        ]
    
    def __str__(self):
        try:
            return f"{self.patient} with {self.doctor} on {self.appointment_date} at {self.start_time}"
        except Exception as e:
            logger.error(f"Error in Appointment.__str__: {e}")
            return f"Appointment {self.pk}"
    
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
            
            max_appointments = getattr(settings, 'MAX_APPOINTMENTS_PER_DAY', 15)
            if appointments_count >= max_appointments:
                raise ValidationError(
                    f'Doctor has reached maximum appointments for this day ({max_appointments})'
                )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


