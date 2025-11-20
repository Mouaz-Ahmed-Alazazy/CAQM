from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, View
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse_lazy
from .admin_services import AdminService
from .models import User
from datetime import datetime


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
    Follows sequence diagram: register_user -> create_user -> create_profile -> notify
    """
    template_name = 'accounts/admin_register_user.html'
    
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
            
            success, result = AdminService.register_user(
                email, password, first_name, last_name, phone, role, **kwargs
            )
            
            if success:
                messages.success(request, f'User {email} registered successfully')
                return redirect('accounts:admin_user_list')
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
    template_name = 'accounts/admin_user_list.html'
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
        
        return redirect('accounts:admin_user_list')
