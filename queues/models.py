from django.db import models
from django.utils import timezone
from doctors.models import Doctor
from patients.models import Patient
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class Queue(models.Model):
    """
    Represents a queue for a specific doctor on a specific date.
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='queues')
    date = models.DateField(default=timezone.now)
    qrcode = models.CharField(max_length=255, blank=True, null=True, help_text="String representation of the QR code data")
    qrcode_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qrcode_generated_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'queues'
        unique_together = ['doctor', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"Queue for {self.doctor} on {self.date}"

    def generate_qrcode(self):
        """
        Generates a unique QR code for the queue.
        The QR code data could be a URL or a unique identifier string.
        Here we use a combination of doctor ID and date.
        """
        qr_data = f"QUEUE-{self.doctor.pk}-{self.date.strftime('%Y%m%d')}"
        self.qrcode = qr_data
        self.qrcode_generated_at = timezone.now()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save image to BytesIO buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        file_name = f"qr_queue_{self.doctor.pk}_{self.date.strftime('%Y%m%d')}.png"
        
        # Save image file to the model field
        self.qrcode_image.save(file_name, File(buffer), save=False)

    def save(self, *args, **kwargs):
        if not self.qrcode_image:
            self.generate_qrcode()
        super().save(*args, **kwargs)

    def get_size(self):
        return self.patient_queues.count()

    def is_empty(self):
        return self.patient_queues.count() == 0
    
    def get_estimated_wait_time(self, position):
        return position * 30
    
    def enqueue(self, patient_id):
        """
        Add a patient to the queue.
        """
        from patients.models import Patient
        
        if isinstance(patient_id, Patient):
            patient = patient_id
        else:
            patient = Patient.objects.get(pk=patient_id)
        
        patient_queue = PatientQueue.objects.create(
            queue=self,
            patient=patient,
            status='WAITING'
        )
        
        return patient_queue
    
    def dequeue(self):
        """
        Remove and return the next patient from the queue (FIFO).
        """
        next_patient = self.patient_queues.filter(
            status='WAITING'
        ).order_by('position').first()
        
        if next_patient:
            next_patient.status = 'IN_PROGRESS'
            next_patient.save()
        
        return next_patient
    
    def validate_qrcode(self, code):
        """
        Validate if a QR code matches this queue.
        """
        return self.qrcode == code
    
    def get_qrcode_image(self):
        """
        Get the QR code image URL.
        """
        if self.qrcode_image:
            return self.qrcode_image.url
        return ""


class PatientQueue(models.Model):
    """
    Represents a patient in a specific queue.
    """
    STATUS_CHOICES = [
        ('WAITING', 'Waiting'),
        ('IN_PROGRESS', 'In Progress'),
        ('TERMINATED', 'Terminated'),
        ('EMERGENCY', 'Emergency'),
        ('NO_SHOW', 'No Show'),
    ]

    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name='patient_queues')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='queue_entries')
    position = models.PositiveIntegerField()
    check_in_time = models.TimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WAITING')
    is_emergency = models.BooleanField(default=False)
    checkedin_via_qrcode = models.BooleanField(default=False)
    
    checkedin_via_qrcode = models.BooleanField(default=False)
    
    consultation_start_time = models.DateTimeField(null=True, blank=True)
    consultation_end_time = models.DateTimeField(null=True, blank=True)
    
    estimated_time = models.IntegerField(help_text="Estimated wait time in minutes", default=0)

    class Meta:
        db_table = 'patient_queues'
        unique_together = ['queue', 'patient']
        ordering = ['position']

    def __str__(self):
        return f"{self.patient} in {self.queue} at position {self.position}"

    def save(self, *args, **kwargs):
        if not self.pk:  # If creating new entry
            # Calculate position
            last_position = PatientQueue.objects.filter(queue=self.queue).aggregate(models.Max('position'))['position__max']
            self.position = (last_position or 0) + 1
            
            # Calculate estimated time
            self.estimated_time = self.queue.get_estimated_wait_time(self.position)
            
        super().save(*args, **kwargs)
    
    def update_status(self, new_status=None):
        """
        Update the patient's queue status.
        """
        if new_status:
            self.status = new_status
        else:
            # Auto-progress status
            if self.status == 'WAITING':
                self.status = 'IN_PROGRESS'
            elif self.status == 'IN_PROGRESS':
                self.status = 'TERMINATED'
        
        self.save()
    
    def get_wait_time(self):
        """
        Calculate current wait time based on check-in time.
        """
        from django.utils import timezone
        from datetime import datetime
        
        if not self.check_in_time:
            return 0
        
        now = timezone.now()
        check_in_datetime = datetime.combine(now.date(), self.check_in_time)
        
        if timezone.is_aware(now):
            check_in_datetime = timezone.make_aware(check_in_datetime)
        
        delta = now - check_in_datetime
        return int(delta.total_seconds() / 60)

    def get_consultation_duration(self):
        """
        Calculate consultation duration in minutes.
        """
        if self.consultation_start_time and self.consultation_end_time:
            delta = self.consultation_end_time - self.consultation_start_time
            return int(delta.total_seconds() / 60)
        return 0
    
    def mark_as_emergency(self):
        """
        Mark this patient as emergency and move to front of queue.
        """
        self.is_emergency = True
        self.status = 'EMERGENCY'
        self.save()
        
        # Move to front (position 1) and shift others
        other_patients = PatientQueue.objects.filter(
            queue=self.queue,
            position__lt=self.position
        ).order_by('position')
        
        for patient_q in other_patients:
            patient_q.position += 1
            patient_q.save()
        
        self.position = 1
        self.save()
    
    def update_position(self, new_position):
        """
        Update patient's position in the queue.
        """
        old_position = self.position
        self.position = new_position
        self.estimated_time = self.queue.get_estimated_wait_time(new_position)
        self.save()
        
        # Adjust other patients' positions
        if new_position < old_position:
            # Moving up - shift others down
            PatientQueue.objects.filter(
                queue=self.queue,
                position__gte=new_position,
                position__lt=old_position
            ).exclude(pk=self.pk).update(position=models.F('position') + 1)
        elif new_position > old_position:
            # Moving down - shift others up
            PatientQueue.objects.filter(
                queue=self.queue,
                position__gt=old_position,
                position__lte=new_position
            ).exclude(pk=self.pk).update(position=models.F('position') - 1)
