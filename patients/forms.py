from django import forms
from doctors.models import Doctor

class AppointmentFilterForm(forms.Form):
    """Form for filtering appointments."""
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + [
            ('SCHEDULED', 'Scheduled'),
            ('CHECKED_IN', 'Checked In'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled'),
            ('NO_SHOW', 'No Show'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.all(),
        required=False,
        empty_label="All Doctors",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
