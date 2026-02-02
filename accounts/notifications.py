import logging
from typing import Dict, Any
from django.core.mail import send_mail
from django.conf import settings
import threading

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Notification service for sending notifications to users.
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
        """
        if notification_type not in cls.NOTIFICATION_TYPES:
            logger.error(f"Invalid notification type: {notification_type}")
            return False
        
        try:
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
            
            # Send actual email if configured
            # Using threading to avoid blocking the main thread (simple async)
            if getattr(settings, 'EMAIL_HOST', None):
                email_thread = threading.Thread(
                    target=cls._send_email_async,
                    args=(subject, message, [user.email])
                )
                email_thread.start()
            
            return True
        except AttributeError as e:
            logger.error(f"Error accessing user attributes: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
            return False
    
    @classmethod
    def send_registration_confirmation(cls, user):
        """Send registration confirmation notification."""
        try:
            return cls.send_notification(user, 'REGISTRATION_CONFIRMATION')
        except Exception as e:
            logger.error(f"Error sending registration confirmation: {e}")
            return False
    
    @classmethod
    def send_booking_confirmation(cls, user, doctor_name: str, date: str, time: str):
        """Send booking confirmation to patient."""
        try:
            return cls.send_notification(
                user,
                'BOOKING_CONFIRMATION',
                context={
                    'doctor_name': doctor_name,
                    'date': date,
                    'time': time
                }
            )
        except Exception as e:
            logger.error(f"Error sending booking confirmation: {e}")
            return False
    
    @classmethod
    def send_new_appointment_notification(cls, user, patient_name: str, date: str, time: str):
        """Send new appointment notification to doctor."""
        try:
            return cls.send_notification(
                user,
                'NEW_APPOINTMENT',
                context={
                    'patient_name': patient_name,
                    'date': date,
                    'time': time
                }
            )
        except Exception as e:
            logger.error(f"Error sending new appointment notification: {e}")
            return False
    @staticmethod
    def _send_email_async(subject, message, recipient_list):
        """Send email asynchronously to avoid blocking response."""
        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@caqm.com')
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_list}: {e}")
