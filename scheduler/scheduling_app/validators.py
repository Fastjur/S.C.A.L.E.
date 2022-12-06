from django.core.exceptions import ValidationError
from django.utils.timezone import now


def validate_not_in_past(value):
    if value < now():
        raise ValidationError("Date cannot be in the past")
