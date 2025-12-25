from django.contrib import admin
from .models import Queue, PatientQueue

@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'created_at', 'qrcode')
    readonly_fields = ('qrcode', 'qrcode_image', 'qrcode_generated_at')

@admin.register(PatientQueue)
class PatientQueueAdmin(admin.ModelAdmin):
    list_display = ('patient', 'queue', 'position', 'status', 'estimated_time')
    list_filter = ('status', 'queue__doctor')
