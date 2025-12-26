from django.db import transaction
from .models import DoctorAvailability
import logging

logger = logging.getLogger(__name__)


class ScheduleService:
    """
    Service layer for doctor schedule management.
    """
    
    @staticmethod
    @transaction.atomic
    def update_schedule(doctor, schedule_data):
        """
        Update doctor's schedule (clear old slots and create new ones).
        """
        try:
            # Clear old slots for the days being updated
            days_to_update = [data['day_of_week'] for data in schedule_data]
            DoctorAvailability.objects.filter(
                doctor=doctor,
                day_of_week__in=days_to_update
            ).delete()
            
            # Create new availability slots
            created_slots = []
            for data in schedule_data:
                availability = DoctorAvailability.objects.create(
                    doctor=doctor,
                    day_of_week=data['day_of_week'],
                    start_time=data['start_time'],
                    end_time=data['end_time'],
                    slot_duration=data.get('slot_duration', 30),
                    is_active=data.get('is_active', True)
                )
                created_slots.append(availability)
            
            return True, f'Successfully created {len(created_slots)} availability slot(s)'
            
        except Exception as e:
            logger.error(f"Error updating schedule for doctor {doctor.pk}: {e}", exc_info=True)
            return False, f'Failed to update schedule: {str(e)}'
    
    @staticmethod
    def get_doctor_schedule(doctor):
        """
        Get doctor's current schedule.
        """
        try:
            return DoctorAvailability.objects.filter(doctor=doctor).order_by('day_of_week')
        except Exception as e:
            logger.error(f"Error getting schedule for doctor {doctor.pk}: {e}")
            return DoctorAvailability.objects.none()
