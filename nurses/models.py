from django.db import models
from django.conf import settings
from doctors.models import Doctor

class Nurse(models.Model):
    """Nurse profile extending User"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='nurse_profile')
    assigned_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='nurses')
    
    class Meta:
        db_table = 'nurses'
    
    def __str__(self):
        return f"Nurse {self.user.get_full_name()}"
