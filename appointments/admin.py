from django.contrib import admin
from .models import Appointment, DoctorAvailability

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'start_time', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'doctor__specialization')
    search_fields = ('patient__user__email', 'doctor__user__email')
    date_hierarchy = 'appointment_date'
    ordering = ('-appointment_date', '-start_time')


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active')
    list_filter = ('day_of_week', 'is_active')
    search_fields = ('doctor__user__email', 'doctor__user__first_name', 'doctor__user__last_name')