from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django import forms
from .models import User, Patient

class PatientRegistrationForm(forms.ModelForm):
    """Inline form for patient registration - no separate forms.py needed"""
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        min_length=8,
        help_text='Password must be at least 8 characters'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '0911234567',
                'pattern': '(091|092|093|094)[0-9]{7}',
                'title': 'Phone number must start with 091, 092, 093, or 094 followed by 7 digits'
            }),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'phone': 'Format: 091xxxxxxx, 092xxxxxxx, 093xxxxxxx, or 094xxxxxxx'
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Ensure phone is exactly 10 digits and starts with correct prefix
            import re
            if not re.match(r'^(091|092|093|094)\d{7}$', phone):
                raise forms.ValidationError(
                    'Phone number must be in format: 091xxxxxxx, 092xxxxxxx, 093xxxxxxx, or 094xxxxxxx'
                )
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role = 'PATIENT'
        
        if commit:
            user.save()
            # Create patient profile
            Patient.objects.create(user=user)
        
        return user


class PatientRegistrationView(CreateView):
    """Patient registration view - only patients can self-register"""
    model = User
    form_class = PatientRegistrationForm
    template_name = 'accounts/patient_register.html'
    success_url = reverse_lazy('appointments:book_appointment')
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect authenticated users
        if request.user.is_authenticated:
            if request.user.is_patient():
                return redirect('appointments:my_appointments')
            elif request.user.is_doctor():
                return redirect('appointments:doctor_dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Auto login after registration
        from django.contrib.auth import login
        login(self.request, self.object, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, 'Registration successful! Welcome to CAQM.')
        return response
    
    def form_invalid(self, form):
        # Don't show generic error message, errors are displayed per field
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    """Custom login view with role-based redirects"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_form(self, form_class=None):
        """Override to customize the form"""
        form = super().get_form(form_class)
        # Customize form fields
        form.fields['username'].label = 'Email'
        form.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email',
            'autofocus': True
        })
        form.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        return form
    
    def get_success_url(self):
        """Redirect based on user role"""
        user = self.request.user
        if user.is_doctor():
            return reverse_lazy('appointments:doctor_dashboard')
        elif user.is_patient():
            return reverse_lazy('appointments:book_appointment')
        else:
            return reverse_lazy('admin:index')
    
    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().get_full_name()}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Don't show generic message, show specific errors
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)