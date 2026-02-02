"""Custom exceptions for appointment operations."""


class AppointmentError(Exception):
    """Base exception for appointment operations."""
    pass


class SlotUnavailableError(AppointmentError):
    """Raised when requested time slot is unavailable."""
    pass


class DoctorUnavailableError(AppointmentError):
    """Raised when doctor has no availability."""
    pass


class MaxAppointmentsError(AppointmentError):
    """Raised when doctor reached max appointments."""
    pass


class InvalidAppointmentError(AppointmentError):
    """Raised when appointment data is invalid."""
    pass
