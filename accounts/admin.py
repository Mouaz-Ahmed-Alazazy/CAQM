from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import User, Patient, Doctor


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
                    level='warning'
                )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """Patient admin - read-only, patients are created via registration"""
    
    list_display = ('get_full_name', 'get_email', 'get_phone', 'get_date_of_birth', 'address')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'user__phone')
    readonly_fields = ('user', 'get_full_name', 'get_email', 'get_phone', 'get_date_of_birth')
    
    def has_add_permission(self, request):
        # Patients can only register via the website
        return False
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_phone(self, obj):
        return obj.user.phone
    get_phone.short_description = 'Phone'
    
    def get_date_of_birth(self, obj):
        return obj.user.date_of_birth
    get_date_of_birth.short_description = 'Date of Birth'


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """Doctor admin - managed by admin only"""
    
    list_display = (
        'get_full_name',
        'specialization',
        'get_email',
        'get_phone',
        'license_number',
        'consultation_fee'
    )
    list_filter = ('specialization',)
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'license_number',
        'specialization'
    )
    readonly_fields = ('user', 'get_full_name', 'get_email')
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'get_full_name', 'get_email')
        }),
        ('Professional Info', {
            'fields': ('specialization', 'license_number', 'bio', 'consultation_fee')
        }),
    )
    
    def has_add_permission(self, request):
        # Doctors must be added via User admin (with inline)
        return False
    
    def get_full_name(self, obj):
        return f"Dr. {obj.user.get_full_name()}"
    get_full_name.short_description = 'Name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_phone(self, obj):
        return obj.user.phone
    get_phone.short_description = 'Phone'


# Customize admin site header
admin.site.site_header = "CAQM Administration"
admin.site.site_title = "CAQM Admin"
admin.site.index_title = "Clinic Appointment & Queue Management System"