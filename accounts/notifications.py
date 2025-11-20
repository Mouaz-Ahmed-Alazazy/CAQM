import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Notification service for sending notifications to users.
    Currently implements logging-based notifications.
    Can be extended to support email, SMS, or push notifications.
    """
    
    NOTIFICATION_TYPES = {
        'REGISTRATION_CONFIRMATION': {
            'subject': 'Welcome to CAQM',
            'template': 'Your account has been created successfully. Welcome to the Clinic Appointment Queue Management System!'
        },
        'BOOKING_CONFIRMATION': {
            'subject': 'Appointment Confirmed',
            'template': 'Your appointment with Dr. {doctor_name} on {date} at {time} has been confirmed.'
        },
        'NEW_APPOINTMENT': {
            'subject': 'New Appointment Scheduled',
            'template': 'A new appointment has been scheduled with {patient_name} on {date} at {time}.'
        }
    }
    
    @classmethod
    def send_notification(cls, user, notification_type: str, context: Dict[str, Any] = None):
        """
        Send a notification to a user.
        
        Args:
            user: User object to send notification to
            notification_type: Type of notification (must be in NOTIFICATION_TYPES)
            context: Additional context data for the notification template
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if notification_type not in cls.NOTIFICATION_TYPES:
            logger.error(f"Invalid notification type: {notification_type}")
            return False
        
        notification_config = cls.NOTIFICATION_TYPES[notification_type]
        subject = notification_config['subject']
        message_template = notification_config['template']
        
        # Fill in template with context data if provided
        if context:
            try:
                message = message_template.format(**context)
            except KeyError as e:
                logger.error(f"Missing template variable: {e}")
                message = message_template
        else:
            message = message_template
        
        # Log the notification
        logger.info(f"""
{'='*60}
NOTIFICATION SENT
{'='*60}
To: {user.email} ({user.get_full_name()})
Subject: {subject}
Message: {message}
Type: {notification_type}
{'='*60}
        """)
        
        # In production, this would send actual email/SMS/push notification
        # For now, we just log it
        
        return True
    
    @classmethod
    def send_registration_confirmation(cls, user):
        """Send registration confirmation notification."""
        return cls.send_notification(user, 'REGISTRATION_CONFIRMATION')
    
    @classmethod
    def send_booking_confirmation(cls, user, doctor_name: str, date: str, time: str):
        """Send booking confirmation to patient."""
        return cls.send_notification(
            user,
            'BOOKING_CONFIRMATION',
            context={
                'doctor_name': doctor_name,
                'date': date,
                'time': time
            }
        )
    
    @classmethod
    def send_new_appointment_notification(cls, user, patient_name: str, date: str, time: str):
        """Send new appointment notification to doctor."""
        return cls.send_notification(
            user,
            'NEW_APPOINTMENT',
            context={
                'patient_name': patient_name,
                'date': date,
                'time': time
            }
        )
