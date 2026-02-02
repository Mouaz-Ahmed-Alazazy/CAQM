"""Date and time helper utilities."""

from datetime import datetime, date, time
from typing import Union
import logging

logger = logging.getLogger(__name__)


def parse_date(date_input: Union[str, date]) -> date:
    """
    Parse date from string or return date object.
    
    Args:
        date_input: Date string in YYYY-MM-DD format or date object
        
    Returns:
        date: Parsed date object
        
    Raises:
        ValueError: If date string is invalid
    """
    if isinstance(date_input, date):
        return date_input
    
    if isinstance(date_input, str):
        try:
            return datetime.strptime(date_input, '%Y-%m-%d').date()
        except ValueError as e:
            logger.error(f"Invalid date format: {date_input}")
            raise ValueError(f"Date must be in YYYY-MM-DD format: {e}")
    
    raise TypeError(f"Expected str or date, got {type(date_input)}")


def parse_time(time_input: Union[str, time]) -> time:
    """
    Parse time from string or return time object.
    
    Args:
        time_input: Time string in HH:MM format or time object
        
    Returns:
        time: Parsed time object
        
    Raises:
        ValueError: If time string is invalid
    """
    if isinstance(time_input, time):
        return time_input
    
    if isinstance(time_input, str):
        try:
            return datetime.strptime(time_input, '%H:%M').time()
        except ValueError as e:
            raise ValueError(f"Time must be in HH:MM format: {e}")
    
    raise TypeError(f"Expected str or time, got {type(time_input)}")


def format_date(date_obj: date, format_str: str = '%Y-%m-%d') -> str:
    """Format date object as string."""
    return date_obj.strftime(format_str)


def format_time(time_obj: time, format_str: str = '%H:%M') -> str:
    """Format time object as string."""
    return time_obj.strftime(format_str)


def format_date_display(date_obj: date) -> str:
    """Format date for display (e.g., 'February 02, 2026')."""
    return date_obj.strftime('%B %d, %Y')


def format_time_display(time_obj: time) -> str:
    """Format time for display (e.g., '02:30 PM')."""
    return time_obj.strftime('%I:%M %p')
