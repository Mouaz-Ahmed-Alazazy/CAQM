import pytest
from datetime import date, time, datetime
from utils.date_helpers import (
    parse_date,
    parse_time,
    format_date,
    format_time,
    format_date_display,
    format_time_display,
)


class TestDateHelpers:
    def test_parse_date_with_date_object(self):
        d = date(2023, 10, 25)
        assert parse_date(d) == d

    def test_parse_date_with_valid_string(self):
        assert parse_date("2023-10-25") == date(2023, 10, 25)

    def test_parse_date_with_invalid_string(self):
        with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD format"):
            parse_date("25-10-2023")

    def test_parse_date_with_invalid_type(self):
        with pytest.raises(TypeError, match="Expected str or date"):
            parse_date(12345)

    def test_parse_time_with_time_object(self):
        t = time(14, 30)
        assert parse_time(t) == t

    def test_parse_time_with_valid_string(self):
        assert parse_time("14:30") == time(14, 30)

    def test_parse_time_with_invalid_string(self):
        with pytest.raises(ValueError, match="Time must be in HH:MM format"):
            parse_time("2:30 PM")

    def test_parse_time_with_invalid_type(self):
        with pytest.raises(TypeError, match="Expected str or time"):
            parse_time(123)

    def test_format_date_default(self):
        d = date(2023, 10, 25)
        assert format_date(d) == "2023-10-25"

    def test_format_date_custom(self):
        d = date(2023, 10, 25)
        assert format_date(d, "%d/%m/%Y") == "25/10/2023"

    def test_format_time_default(self):
        t = time(14, 30)
        assert format_time(t) == "14:30"

    def test_format_time_custom(self):
        t = time(14, 30)
        assert format_time(t, "%I:%M %p") == "02:30 PM"

    def test_format_date_display(self):
        d = date(2023, 10, 25)
        assert format_date_display(d) == "October 25, 2023"

    def test_format_time_display(self):
        t1 = time(14, 30)
        assert format_time_display(t1) == "02:30 PM"

        t2 = time(9, 5)
        assert format_time_display(t2) == "09:05 AM"
