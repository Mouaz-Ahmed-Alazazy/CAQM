from django.urls import path
from .views import AdminUserRegistrationView, AdminUserListView, AdminDeleteUserView, AdminDashboardView

app_name = 'admins'

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('dashboard/', AdminDashboardView.as_view(), name='dashboard'),
    path('register-user/', AdminUserRegistrationView.as_view(), name='admin_register_user'),
    path('users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('users/delete/<int:user_id>/', AdminDeleteUserView.as_view(), name='admin_delete_user'),
]
