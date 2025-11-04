from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Base user model for all user types"""
    
    ROLE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('ADMIN', 'Admin'),
    ]
    
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    ]
    
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,13}$',
        message="Phone number must be entered in the format: '+999999999999'. Up to 13 digits allowed."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='PATIENT')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'date_of_birth']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return self.first_name
    
    def is_patient(self):
        return self.role == 'PATIENT'
    
    def is_doctor(self):
        return self.role == 'DOCTOR'
    
    def is_admin(self):
        return self.role == 'ADMIN'


class Patient(models.Model):
    """Patient profile extending User"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='patient_profile')
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=17, blank=True)
    
    class Meta:
        db_table = 'patients'
    
    def __str__(self):
        return self.user.get_full_name()


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
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='doctor_profile')
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