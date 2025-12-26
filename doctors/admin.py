from django.contrib import admin
from .models import Doctor, DoctorAvailability

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


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active')
    list_filter = ('day_of_week', 'is_active')
    search_fields = ('doctor__user__email', 'doctor__user__first_name', 'doctor__user__last_name')