from django.urls import path
from .views import PatientRegistrationView, CustomLoginView, CustomLogoutView, ProfileUpdateView

app_name = 'accounts'

urlpatterns = [
    path('register/', PatientRegistrationView.as_view(), name='patient_register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
]