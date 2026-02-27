"""
URL configuration for the doctors app.
"""
from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.DoctorDashboardView.as_view(), name='doctor_dashboard'),

    # Appointments
    path('today-appointments/', views.TodayAppointmentsView.as_view(),
         name='today_appointments'),
    path('upcoming-appointments/', views.UpcomingAppointmentsView.as_view(),
         name='upcoming_appointments'),

    # Availability management
    path('availability/', views.AvailabilityManagementView.as_view(),
         name='availability_management'),
    path('availability/delete/<int:availability_id>/',
         views.DeleteAvailabilityView.as_view(), name='delete_availability'),

    # Queue Routing
    path('queue-redirect/', views.DoctorQueueRedirectView.as_view(),
         name='queue_redirect'),

    # Patient Medical Form
    path('patient-form/<int:patient_id>/',
         views.PatientMedicalFormView.as_view(), name='patient_medical_form'),
]
