from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, View, TemplateView
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from .services import AdminService, AdminDashboardService
from accounts.models import User
from datetime import datetime, timedelta


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only admins can access the view"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()
    
    def handle_no_permission(self):
        messages.error(self.request, 'Only administrators can access this page')
        return redirect('accounts:login')


class AdminUserRegistrationView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    Admin can register new users (Patient, Doctor, Admin).
    """
    template_name = 'admins/admin_register_user.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        try:
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone = request.POST.get('phone')
            role = request.POST.get('role')
            
            # Validate required fields
            if not all([email, password, first_name, last_name, phone, role]):
                messages.error(request, 'All fields are required')
                return render(request, self.template_name)
            
            # Role-specific data
            kwargs = {}
            if role == 'PATIENT':
                dob_str = request.POST.get('date_of_birth')
                if dob_str:
                    kwargs['date_of_birth'] = datetime.strptime(dob_str, '%Y-%m-%d').date()
                kwargs['address'] = request.POST.get('address', '')
                kwargs['emergency_contact'] = request.POST.get('emergency_contact', '')
            elif role == 'DOCTOR':
                kwargs['specialization'] = request.POST.get('specialization')
                kwargs['license_number'] = request.POST.get('license_number', '')
                kwargs['years_of_experience'] = int(request.POST.get('years_of_experience', 0))
            elif role == 'NURSE':
                assigned_doctor_id = request.POST.get('assigned_doctor')
                if assigned_doctor_id:
                    try:
                        from doctors.models import Doctor
                        kwargs['assigned_doctor'] = Doctor.objects.get(pk=assigned_doctor_id)
                    except Doctor.DoesNotExist:
                        messages.warning(request, 'Selected doctor not found. Nurse will be created without assigned doctor.')
            
            success, result = AdminService.register_user(
                email, password, first_name, last_name, phone, role, **kwargs
            )
            
            if success:
                messages.success(request, f'User {email} registered successfully')
                return redirect('admins:admin_user_list')
            else:
                messages.error(request, result)
                return render(request, self.template_name)
                
        except Exception as e:
            messages.error(request, f'Error registering user: {str(e)}')
            return render(request, self.template_name)


class AdminUserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """
    List all users with filtering by role.
    """
    model = User
    template_name = 'admins/admin_user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        role_filter = self.request.GET.get('role')
        return AdminService.get_all_users(role=role_filter)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_filter'] = self.request.GET.get('role', '')
        return context


class AdminDeleteUserView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Delete a user"""
    
    def post(self, request, user_id):
        try:
            success, message = AdminService.delete_user(user_id)
            
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
                
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
        
        return redirect('admins:admin_user_list')


class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """
    Admin dashboard overview page.
    Shows high-level statistics and today's summary.
    """
    template_name = 'admins/admin_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        
        # Get overview statistics and today's summary only
        context['overview'] = AdminDashboardService.get_overview_stats()
        context['today_summary'] = AdminDashboardService.get_today_summary()
        context['today'] = today
        
        return context


class AdminQueueStatsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """
    Queue statistics page with filtering.
    Shows detailed doctor queue statistics with past, present, and future data.
    """
    template_name = 'admins/admin_queue_stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from query params
        date_from_str = self.request.GET.get('date_from')
        date_to_str = self.request.GET.get('date_to')
        
        today = timezone.now().date()
        
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else today - timedelta(days=30)
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else today + timedelta(days=30)
        except ValueError:
            date_from = today - timedelta(days=30)
            date_to = today + timedelta(days=30)
        
        # Get doctor statistics
        context['doctor_stats'] = AdminDashboardService.get_doctor_queue_stats(date_from, date_to)
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['today'] = today
        
        return context


class AdminActivityLogView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """
    Recent activity log page with pagination.
    Shows recent queue activity across all doctors.
    """
    template_name = 'admins/admin_activity_log.html'
    context_object_name = 'activities'
    paginate_by = 20
    
    def get_queryset(self):
        return AdminDashboardService.get_recent_activity(limit=100)
