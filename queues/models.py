from django.db import models
from django.utils import timezone
from accounts.models import Doctor, Patient
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
        # Simple estimation: position * average_consultation_time (e.g., 15 mins)
        # This can be refined based on actual data
        return position * 15


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
