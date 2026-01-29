from django.urls import path
from .views import GetAvailableSlotsView, GetDoctorAvailabilityView

app_name = 'appointments'

urlpatterns = [
    # Shared AJAX endpoint for available slots
    path('available-slots/', GetAvailableSlotsView.as_view(), name='get_available_slots'),
    # AJAX endpoint to get doctor's weekly schedule
    path('doctor-availability/', GetDoctorAvailabilityView.as_view(), name='get_doctor_availability'),
]