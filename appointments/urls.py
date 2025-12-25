from django.urls import path
from .views import GetAvailableSlotsView

app_name = 'appointments'

urlpatterns = [
    # Shared AJAX endpoint for available slots
    path('available-slots/', GetAvailableSlotsView.as_view(), name='get_available_slots'),
]