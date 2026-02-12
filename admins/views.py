from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, View, TemplateView
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from .services import AdminService, AdminDashboardService, AdminAppointmentService
from accounts.models import User
from doctors.models import Doctor
from patients.models import Patient
from nurses.models import Nurse
from datetime import datetime, timedelta


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only admins can access the view"""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()

    def handle_no_permission(self):
        messages.error(
            self.request, 'Only administrators can access this page')
        return redirect('accounts:login')


class AdminUserRegistrationView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admins/admin_register_user.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            role = request.POST.get('role')

            if not all([email, password, first_name, last_name, phone, role]):
                messages.error(request, 'All fields are required')
                return render(request, self.template_name)

            if User.objects.filter(email=email).exists():
                messages.error(
                    request, 'A user with this email already exists')
                return render(request, self.template_name)

            import re
            if not re.match(r'^[0-9]{10,15}$', phone):
                messages.error(request, 'Phone number must be 10-15 digits')
                return render(request, self.template_name)

            if len(password) < 8:
                messages.error(
                    request, 'Password must be at least 8 characters')
                return render(request, self.template_name)

            kwargs = {}

            dob_str = request.POST.get('date_of_birth')
            if dob_str:
                try:
                    kwargs['date_of_birth'] = datetime.strptime(
                        dob_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, 'Invalid date of birth format')
                    return render(request, self.template_name)
            else:
                messages.error(request, 'Date of birth is required')
                return render(request, self.template_name)

            kwargs['gender'] = request.POST.get('gender', 'MALE')

            if role == 'PATIENT':
                kwargs['address'] = request.POST.get('address', '')
                kwargs['emergency_contact'] = request.POST.get(
                    'emergency_contact', '')
            elif role == 'DOCTOR':
                specialization = request.POST.get('specialization')
                if not specialization:
                    messages.error(
                        request, 'Specialization is required for doctors')
                    return render(request, self.template_name)
                kwargs['specialization'] = specialization
                kwargs['license_number'] = request.POST.get(
                    'license_number', '')
            elif role == 'NURSE':
                assigned_doctor_id = request.POST.get('assigned_doctor')
                if assigned_doctor_id:
                    try:
                        kwargs['assigned_doctor'] = Doctor.objects.get(
                            pk=assigned_doctor_id)
                    except Doctor.DoesNotExist:
                        messages.warning(
                            request, 'Selected doctor not found. Nurse will be created without assigned doctor.')

            success, result = AdminService.register_user(
                email, password, first_name, last_name, phone, role, **kwargs
            )

            if success:
                messages.success(
                    request, f'User {email} registered successfully')
                return redirect('admins:admin_user_list')
            else:
                messages.error(request, result)
                return render(request, self.template_name)

        except Exception as e:
            messages.error(request, f'Error registering user: {str(e)}')
            return render(request, self.template_name)


class AdminUserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'admins/admin_user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        role_filter = self.request.GET.get('role')
        search = self.request.GET.get('search', '').strip()
        return AdminService.get_all_users(role=role_filter, search=search or None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_filter'] = self.request.GET.get('role', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class AdminDeleteUserView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, user_id):
        try:
            if user_id == request.user.id:
                messages.error(request, 'You cannot delete your own account')
                return redirect('admins:admin_user_list')

            success, message = AdminService.delete_user(user_id)

            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)

        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')

        return redirect('admins:admin_user_list')


class AdminEditUserView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'admins/admin_edit_user.html'

    def _get_user(self, user_id):
        return User.objects.filter(pk=user_id).first()

    def _get_context(self, user):
        context = {
            'edit_user': user,
            'doctors': Doctor.objects.select_related('user').all(),
            'patient_profile': Patient.objects.filter(user=user).first() if user.role == 'PATIENT' else None,
            'doctor_profile': Doctor.objects.filter(user=user).first() if user.role == 'DOCTOR' else None,
            'nurse_profile': Nurse.objects.filter(user=user).first() if user.role == 'NURSE' else None,
        }
        return context

    def get(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            messages.error(request, 'User not found')
            return redirect('admins:admin_user_list')
        return render(request, self.template_name, self._get_context(user))

    def post(self, request, user_id):
        user = self._get_user(user_id)
        if not user:
            messages.error(request, 'User not found')
            return redirect('admins:admin_user_list')

        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', 'MALE')
        dob_str = request.POST.get('date_of_birth')

        if not all([email, first_name, last_name, phone, gender, dob_str]):
            messages.error(request, 'All required fields must be filled')
            return render(request, self.template_name, self._get_context(user))

        import re
        if not re.match(r'^[0-9]{10,15}$', phone):
            messages.error(request, 'Phone number must be 10-15 digits')
            return render(request, self.template_name, self._get_context(user))

        try:
            date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date of birth format')
            return render(request, self.template_name, self._get_context(user))

        extra_kwargs = {}
        if user.role == 'PATIENT':
            extra_kwargs['address'] = request.POST.get('address', '')
            extra_kwargs['emergency_contact'] = request.POST.get(
                'emergency_contact', '')
        elif user.role == 'DOCTOR':
            specialization = request.POST.get('specialization', '')
            if not specialization:
                messages.error(
                    request, 'Specialization is required for doctors')
                return render(request, self.template_name, self._get_context(user))
            extra_kwargs['specialization'] = specialization
            extra_kwargs['license_number'] = request.POST.get(
                'license_number', '')
        elif user.role == 'NURSE':
            assigned_doctor_id = request.POST.get('assigned_doctor')
            if assigned_doctor_id:
                try:
                    extra_kwargs['assigned_doctor'] = Doctor.objects.get(
                        pk=assigned_doctor_id)
                except Doctor.DoesNotExist:
                    messages.error(
                        request, 'Selected assigned doctor was not found')
                    return render(request, self.template_name, self._get_context(user))
            else:
                extra_kwargs['assigned_doctor'] = None

        success, result = AdminService.update_user_profile(
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            date_of_birth=date_of_birth,
            gender=gender,
            **extra_kwargs,
        )

        if success:
            messages.success(
                request, f'Profile updated successfully for {result.email}')
            return redirect('admins:admin_user_list')

        messages.error(request, result)
        return render(request, self.template_name, self._get_context(user))


class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'admins/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context['overview'] = AdminDashboardService.get_overview_stats()
        context['today_summary'] = AdminDashboardService.get_today_summary()
        context['today'] = today
        return context


class AdminQueueStatsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'admins/admin_queue_stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_from_str = self.request.GET.get('date_from')
        date_to_str = self.request.GET.get('date_to')
        today = timezone.now().date()

        try:
            date_from = datetime.strptime(
                date_from_str, '%Y-%m-%d').date() if date_from_str else today - timedelta(days=30)
            date_to = datetime.strptime(
                date_to_str, '%Y-%m-%d').date() if date_to_str else today + timedelta(days=30)
        except ValueError:
            date_from = today - timedelta(days=30)
            date_to = today + timedelta(days=30)

        context['doctor_stats'] = AdminDashboardService.get_doctor_queue_stats(
            date_from, date_to)
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['today'] = today
        return context


class AdminActivityLogView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    template_name = 'admins/admin_activity_log.html'
    context_object_name = 'activities'
    paginate_by = 20

    def get_queryset(self):
        search = self.request.GET.get('search', '').strip() or None
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        status = self.request.GET.get('status') or None

        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            except ValueError:
                date_from = None
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                date_to = None

        return AdminDashboardService.get_recent_activity(
            search=search, date_from=date_from, date_to=date_to, status=status
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['status_choices'] = [
            ('', 'All Statuses'),
            ('WAITING', 'Waiting'),
            ('IN_PROGRESS', 'In Progress'),
            ('TERMINATED', 'Completed'),
            ('NO_SHOW', 'No Show'),
            ('EMERGENCY', 'Emergency'),
        ]
        return context


class AdminManageAppointmentsView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    template_name = 'admins/admin_manage_appointments.html'
    context_object_name = 'appointments'
    paginate_by = 20

    def get_queryset(self):
        doctor_id = self.request.GET.get('doctor')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        status = self.request.GET.get('status')

        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            except ValueError:
                date_from = None
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                date_to = None

        return AdminAppointmentService.get_appointments(
            doctor_id=doctor_id,
            date_from=date_from,
            date_to=date_to,
            status=status,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doctors'] = Doctor.objects.select_related('user').all()
        context['status_choices'] = [
            ('', 'All Statuses'),
            ('SCHEDULED', 'Scheduled'),
            ('CHECKED_IN', 'Checked In'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled'),
            ('NO_SHOW', 'No Show'),
        ]
        context['today'] = timezone.now().date()
        context['selected_doctor'] = self.request.GET.get('doctor', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        return context


class AdminCancelAppointmentView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, appointment_id):
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(
                request, 'A reason is required to cancel an appointment')
            return redirect('admins:admin_manage_appointments')
        success, message = AdminAppointmentService.cancel_single_appointment(
            appointment_id, reason=reason
        )

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect('admins:admin_manage_appointments')


class AdminCancelDoctorAppointmentsView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request):
        doctor_id = request.POST.get('doctor_id')
        date_str = request.POST.get('date')
        reason = request.POST.get('reason', '').strip()

        if not reason:
            messages.error(
                request, 'A reason is required for bulk cancellation')
            return redirect('admins:admin_manage_appointments')

        if not doctor_id:
            messages.error(request, 'Please select a doctor')
            return redirect('admins:admin_manage_appointments')

        date = None
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Invalid date format')
                return redirect('admins:admin_manage_appointments')

        success, message, count = AdminAppointmentService.cancel_doctor_appointments(
            doctor_id, date=date, reason=reason
        )

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect('admins:admin_manage_appointments')
