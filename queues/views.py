"""
Views for Queue Check-in functionality.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views import View
from .services import CheckInService
import json


class QRScannerView(LoginRequiredMixin, TemplateView):
    """
    Display QR scanner interface for check-in.
    Mobile-optimized page with camera access.
    """
    template_name = 'queues/qr_scanner.html'
    
    def get_context_data(self, kwargs):
        context = super().get_context_data(kwargs)
        context['user'] = self.request.user
        context['user_type'] = 'Doctor' if self.request.user.is_doctor() else 'Patient'
        return context


class ProcessCheckInView(LoginRequiredMixin, View):
    """
    Process check-in after QR code is scanned.
    Accepts POST request with QR code data.
    """
    
    def post(self, request, *args, **kwargs):
        """Handle check-in request"""
        try:
            # Parse JSON body
            data = json.loads(request.body)
            qr_data = data.get('qr_data', '').strip()
            
            if not qr_data:
                return JsonResponse({
                    'success': False,
                    'message': 'No QR code data provided.'
                }, status=400)
            
            # Process check-in through service layer
            result = CheckInService.process_check_in(request.user, qr_data)
            
            # Return JSON response
            status_code = 200 if result['success'] else 400
            return JsonResponse(result, status=status_code)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid request format.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            }, status=500)