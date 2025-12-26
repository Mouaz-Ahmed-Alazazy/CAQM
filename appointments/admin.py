from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'start_time', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'doctor__specialization')
    search_fields = ('patient__user__email', 'doctor__user__email')
    date_hierarchy = 'appointment_date'
    ordering = ('-appointment_date', '-start_time')

