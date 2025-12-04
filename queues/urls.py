"""
URL configuration for queues app.
"""
from django.urls import path
from .views import QRScannerView, ProcessCheckInView, PatientQueueStatusView
from .nurse_views import NurseDashboardView, StartConsultationView, EndConsultationView

app_name = 'queues'

urlpatterns = [
    path('scan/', QRScannerView.as_view(), name='qr_scanner'),
    path('checkin/', ProcessCheckInView.as_view(), name='process_checkin'),
    path('status/', PatientQueueStatusView.as_view(), name='queue_status'),
    
    # Nurse URLs
    path('nurse/dashboard/', NurseDashboardView.as_view(), name='nurse_dashboard'),
    path('nurse/start-consultation/<int:pk>/', StartConsultationView.as_view(), name='start_consultation'),
    path('nurse/end-consultation/<int:pk>/', EndConsultationView.as_view(), name='end_consultation'),
]