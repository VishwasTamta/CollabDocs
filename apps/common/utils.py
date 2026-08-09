from datetime import datetime, time

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework.exceptions import ValidationError


def parse_timestamp(value, field_name):
    """
    Turn an ISO date or datetime query parameter into an aware datetime.

    Raises a DRF ValidationError - so the client gets a 400 rather than a 500 -
    when the value is not a date Django can read.
    """

    parsed = parse_datetime(value) or parse_date(value)

    if parsed is None:
        raise ValidationError(
            {
                field_name: (
                    "Expected an ISO date or datetime, "
                    "e.g. 2026-08-09 or 2026-08-09T10:30:00Z."
                )
            }
        )

    if not isinstance(parsed, datetime):
        parsed = datetime.combine(parsed, time.min)

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)

    return parsed
