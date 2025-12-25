from django.contrib import admin
from .models import Patient

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
