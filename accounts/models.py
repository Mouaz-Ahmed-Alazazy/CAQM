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
        ('NURSE', 'Nurse'),
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
        regex=r'^(091|092|093|094)\d{7}$',
        message="Phone number must be in the format: '091xxxxxxx', '092xxxxxxx', '093xxxxxxx', or '094xxxxxxx' (10 digits total)."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, default='')
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
    
    def is_nurse(self):
        return self.role == 'NURSE'

