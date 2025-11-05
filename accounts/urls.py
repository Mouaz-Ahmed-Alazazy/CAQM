from django.urls import path
from .views import PatientRegistrationView, CustomLoginView, CustomLogoutView

app_name = 'accounts'

urlpatterns = [
    path('register/', PatientRegistrationView.as_view(), name='patient_register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]