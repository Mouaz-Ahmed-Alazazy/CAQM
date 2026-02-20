from django.urls import path
from .views import (
    AdminUserRegistrationView,
    AdminUserListView,
    AdminEditUserView,
    AdminDeleteUserView,
    AdminDashboardView,
    AdminQueueStatsView,
    AdminActivityLogView,
    AdminManageAppointmentsView,
    AdminCancelAppointmentView,
    AdminCancelDoctorAppointmentsView,
    AdminBookAppointmentView,
    AdminBookEmergencyView,
)
from .api import DoctorListAPIView

app_name = 'admins'

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('queue-stats/', AdminQueueStatsView.as_view(), name='admin_queue_stats'),
    path('activity-log/', AdminActivityLogView.as_view(),
         name='admin_activity_log'),
    path('register-user/', AdminUserRegistrationView.as_view(),
         name='admin_register_user'),
    path('users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('users/edit/<int:user_id>/', AdminEditUserView.as_view(),
         name='admin_edit_user'),
    path('users/delete/<int:user_id>/',
         AdminDeleteUserView.as_view(), name='admin_delete_user'),
    path('appointments/', AdminManageAppointmentsView.as_view(),
         name='admin_manage_appointments'),
    path('appointments/cancel/<int:appointment_id>/',
         AdminCancelAppointmentView.as_view(), name='admin_cancel_appointment'),
    path('appointments/cancel-doctor/', AdminCancelDoctorAppointmentsView.as_view(),
         name='admin_cancel_doctor_appointments'),
    path('book-appointment/', AdminBookAppointmentView.as_view(),
         name='admin_book_appointment'),
    path('book-emergency/', AdminBookEmergencyView.as_view(),
         name='admin_book_emergency'),
    path('api/doctors/', DoctorListAPIView.as_view(), name='api_doctors'),
]
