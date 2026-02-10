from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('book/', views.BookAppointmentView.as_view(), name='book_appointment'),
    path('my-appointments/', views.MyAppointmentsView.as_view(), name='my_appointments'),
    path('modify/<int:pk>/', views.ModifyAppointmentView.as_view(), name='modify_appointment'),
    path('cancel/<int:pk>/', views.CancelAppointmentView.as_view(), name='cancel_appointment'),
    path('patient-form/submit/', views.SubmitPatientFormView.as_view(), name='submit_patient_form'),
    path('notifications/', views.PatientNotificationsView.as_view(), name='notifications'),
    path('notifications/<int:notification_id>/read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),
]
