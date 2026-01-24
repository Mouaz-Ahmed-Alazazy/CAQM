from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import User
from doctors.models import Doctor
from nurses.models import Nurse


class CustomUserCreationForm(UserCreationForm):
    """Custom form for creating users in admin"""
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'date_of_birth', 'gender', 'role')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default role to DOCTOR when creating from admin
        if not self.instance.pk:  # New user
            self.fields['role'].initial = 'DOCTOR'


class DoctorInline(admin.StackedInline):
    """Inline form for doctor profile"""
    model = Doctor
    can_delete = False
    verbose_name_plural = 'Doctor Profile'
    fields = ('specialization', 'license_number', 'bio', 'consultation_fee')
    
    def has_add_permission(self, request, obj=None):
        # Only show for users with DOCTOR role
        if obj and obj.role == 'DOCTOR':
            return True
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with doctor creation support"""
    
    add_form = CustomUserCreationForm
    form = UserChangeForm
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'gender')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone', 'date_of_birth', 'gender')
        }),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'phone',
                'date_of_birth',
                'gender',
                'role',
                'password1',
                'password2',
            ),
        }),
        ('Doctor Info (only for doctors)', {
            'classes': ('collapse',),
            'description': 'Fill this section only if creating a doctor account',
            'fields': (),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    # Show doctor inline only for doctor users
    def get_inline_instances(self, request, obj=None):
        if obj and obj.role == 'DOCTOR':
            return [DoctorInline(self.model, self.admin_site)]
        return []
    
    def save_model(self, request, obj, form, change):
        """Auto-create doctor profile when role is DOCTOR"""
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        
        # If new user with DOCTOR role, create doctor profile
        if is_new and obj.role == 'DOCTOR':
            if not hasattr(obj, 'doctor_profile'):
                Doctor.objects.create(
                    user=obj,
                    specialization='GENERAL'
                )
                self.message_user(
                    request,
                    f'Doctor profile created for {obj.get_full_name()}. Please update specialization and other details.',
                    level='info'
                )
        
        # If new user with NURSE role, create nurse profile
        elif is_new and obj.role == 'NURSE':
            if not hasattr(obj, 'nurse_profile'):
                Nurse.objects.create(user=obj)
                self.message_user(
                    request,
                    f'Nurse profile created for {obj.get_full_name()}.',
                    level='info'
                )



# Customize admin site header
admin.site.site_header = "CAQM Administration"
admin.site.site_title = "CAQM Admin"
admin.site.index_title = "Clinic Appointment & Queue Management System"