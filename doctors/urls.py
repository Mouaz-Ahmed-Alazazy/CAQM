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
    path('today-appointments/', views.TodayAppointmentsView.as_view(), name='today_appointments'),
    path('upcoming-appointments/', views.UpcomingAppointmentsView.as_view(), name='upcoming_appointments'),
    
    # Availability management
    path('availability/', views.AvailabilityManagementView.as_view(), name='availability_management'),
    path('availability/delete/<int:availability_id>/', views.DeleteAvailabilityView.as_view(), name='delete_availability'),
]
