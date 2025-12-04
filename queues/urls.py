"""
URL configuration for queues app.
"""
from django.urls import path
from .views import QRScannerView, ProcessCheckInView, PatientQueueStatusView

app_name = 'queues'

urlpatterns = [
    path('scan/', QRScannerView.as_view(), name='qr_scanner'),
    path('checkin/', ProcessCheckInView.as_view(), name='process_checkin'),
    path('status/', PatientQueueStatusView.as_view(), name='queue_status'),
]