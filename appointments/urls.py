from django.urls import path
from .views import (
    BookAppointmentView,
    GetAvailableSlotsView,
    MyAppointmentsView,
    DoctorDashboardView,
    DeleteAvailabilityView
)

app_name = 'appointments'

urlpatterns = [
    path('book/', BookAppointmentView.as_view(), name='book_appointment'),
    path('my-appointments/', MyAppointmentsView.as_view(), name='my_appointments'),
    path('available-slots/', GetAvailableSlotsView.as_view(), name='get_available_slots'),
    path('doctor/dashboard/', DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('doctor/availability/delete/<int:availability_id>/', 
         DeleteAvailabilityView.as_view(), 
         name='delete_availability'),
]