from django.urls import path
from .views import PatientRegistrationView, CustomLoginView, CustomLogoutView
from .admin_views import AdminUserRegistrationView, AdminUserListView, AdminDeleteUserView

app_name = 'accounts'

urlpatterns = [
    path('register/', PatientRegistrationView.as_view(), name='patient_register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(next_page='accounts:login'), name='logout'),
    # Admin features
    path('admin/register-user/', AdminUserRegistrationView.as_view(), name='admin_register_user'),
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/delete/<int:user_id>/', AdminDeleteUserView.as_view(), name='admin_delete_user'),
]