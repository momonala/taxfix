"""Data anonymization functions."""

import logging
from datetime import datetime

from email_validator import EmailNotValidError, validate_email

from src.database import AnonymizedPerson
from src.fetch_data import Person

logger = logging.getLogger(__name__)


def calculate_age_group(birthday: str) -> str | None:
    """
    Calculate age group from birthday in format YYYY-MM-DD.

    Args:
        birthday: Date string in YYYY-MM-DD format

    Returns:
        Age group string in format [X-Y] where X and Y are multiples of 10

    Raises:
        ValueError: If birthday is in the future
    """
    try:
        birth_date = datetime.strptime(birthday, "%Y-%m-%d")
    except ValueError as e:
        logger.error(f"Error calculating age group: {e}")
        return None

    today = datetime.now()

    if birth_date > today:
        raise ValueError(f"Birthday {birthday} is in the future")

    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    lower_bound = (age // 10) * 10
    upper_bound = lower_bound + 10

    return f"[{lower_bound}-{upper_bound}]"


def extract_email_domain(email: str | None) -> str | None:
    """
    Extract domain from email address using email-validator for robust validation.

    Args:
        email: Complete email address or None

    Returns:
        Email domain or None if email is invalid or None
    """
    if email is None:
        return None

    try:
        email_info = validate_email(email, check_deliverability=False)
        return email_info.domain
    except EmailNotValidError:
        return None


def anonymize_person(person: Person) -> AnonymizedPerson:
    """Anonymize a person and return an SQLAlchemy model instance.

    Args:
        person: Person data from the API

    Returns:
        AnonymizedPerson SQLAlchemy model instance
    """
    return AnonymizedPerson(
        age_group=calculate_age_group(person.birthday),
        email_domain=extract_email_domain(person.email),
        country=person.address.country,
        city=person.address.city,
    )
