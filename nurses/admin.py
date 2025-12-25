from django.contrib import admin
from .models import Nurse

@admin.register(Nurse)
class NurseAdmin(admin.ModelAdmin):
    """Nurse admin - managed by admin only"""
    
    list_display = ('get_full_name', 'assigned_doctor', 'get_email', 'get_phone')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('user', 'get_full_name', 'get_email')
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'get_full_name', 'get_email')
        }),
        ('Professional Info', {
            'fields': ('assigned_doctor',)
        }),
    )
    
    def has_add_permission(self, request):
        # Nurses must be added via User admin (with inline or logical creation)
        return False
    
    def get_full_name(self, obj):
        return f"Nurse {obj.user.get_full_name()}"
    get_full_name.short_description = 'Name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_phone(self, obj):
        return obj.user.phone
    get_phone.short_description = 'Phone'
