"""
URL configuration for queues app.
"""
from django.urls import path
from . import views
from .views import QRScannerView, ProcessCheckInView, PatientQueueStatusView, CallNextPatientView, QueueStatusAPIView

app_name = 'queues'

urlpatterns = [
    path('scan/', QRScannerView.as_view(), name='qr_scanner'),
    path('checkin/', ProcessCheckInView.as_view(), name='process_checkin'),
    path('status/', PatientQueueStatusView.as_view(), name='queue_status'),
    path('api/status/', QueueStatusAPIView.as_view(), name='queue_status_api'),
    path('call-next/', CallNextPatientView.as_view(), name='call_next_patient'),
]