"""
URL configuration for the nurses app.
"""
from django.urls import path
from . import views

app_name = 'nurses'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.NurseDashboardView.as_view(), name='nurse_dashboard'),
    
    # Queue Management
    path('queue/', views.QueueManagementView.as_view(), name='queue_management'),
    path('queue/call-next/', views.CallNextPatientView.as_view(), name='call_next_patient'),
    
    # Consultation Management
    path('consultation/<int:pk>/start/', views.StartConsultationView.as_view(), name='start_consultation'),
    path('consultation/<int:pk>/end/', views.EndConsultationView.as_view(), name='end_consultation'),
    
    # Patient Status
    path('patient/<int:pk>/no-show/', views.MarkNoShowView.as_view(), name='mark_no_show'),
]
