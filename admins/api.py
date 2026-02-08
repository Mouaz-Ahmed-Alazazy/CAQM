from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from doctors.models import Doctor
from .views import AdminRequiredMixin


class DoctorListAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API view to fetch doctors list for nurse assignment (admin only)"""
    
    def get(self, request):
        doctors = Doctor.objects.select_related('user').all()
        data = [
            {
                'id': doctor.pk,
                'name': doctor.user.get_full_name(),
                'specialization': doctor.get_specialization_display()
            }
            for doctor in doctors
        ]
        return JsonResponse(data, safe=False)
