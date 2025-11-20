from django.urls import path
from .views import (
    BookAppointmentView,
    GetAvailableSlotsView,
    MyAppointmentsView,
    DoctorDashboardView,
    DeleteAvailabilityView,
    ModifyAppointmentView,
    CancelAppointmentView,
    SubmitPatientFormView
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
    # New features
    path('modify/<int:pk>/', ModifyAppointmentView.as_view(), name='modify_appointment'),
    path('cancel/<int:pk>/', CancelAppointmentView.as_view(), name='cancel_appointment'),
    path('patient-form/submit/', SubmitPatientFormView.as_view(), name='submit_patient_form'),
]