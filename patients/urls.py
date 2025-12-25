from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    # Appointment booking
    path('book/', views.BookAppointmentView.as_view(), name='book_appointment'),
    path('my-appointments/', views.MyAppointmentsView.as_view(), name='my_appointments'),
    path('modify/<int:pk>/', views.ModifyAppointmentView.as_view(), name='modify_appointment'),
    path('cancel/<int:pk>/', views.CancelAppointmentView.as_view(), name='cancel_appointment'),
    
    # Medical forms
    path('patient-form/submit/', views.SubmitPatientFormView.as_view(), name='submit_patient_form'),
]
