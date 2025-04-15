"""Tests for data anonymization functions."""

import pytest
from freezegun import freeze_time

from src.data_anonymization import (
    anonymize_person,
    calculate_age_group,
    extract_email_domain,
)
from src.database import AnonymizedPerson
from src.fetch_data import Person, Address

# Create a sample address for reuse in tests
SAMPLE_ADDRESS = Address(
    id="addr123",
    street="123 Main St",
    streetName="Main St",
    buildingNumber="123",
    city="New York",
    zipcode="10001",
    country="USA",
    country_code="US",
    latitude=40.7128,
    longitude=-74.0060,
)

EMPTY_ADDRESS = Address(
    id="",
    street="",
    streetName="",
    buildingNumber="",
    city="",
    zipcode="",
    country="",
    country_code="",
    latitude=0.0,
    longitude=0.0,
)


@pytest.mark.parametrize(
    "birthday,expected_age_group,frozen_date",
    [
        # Current year tests with frozen datetime.now() at 2025-01-01
        ("2025-01-01", "[0-10]", "2025-01-01"),
        ("1999-01-01", "[20-30]", "2025-01-01"),
        ("1989-01-01", "[30-40]", "2025-01-01"),
        ("1979-01-01", "[40-50]", "2025-01-01"),
        # Age group boundary tests
        ("2025-01-01", "[0-10]", "2025-01-01"),  # Same day, should not raise error
        ("2015-01-02", "[0-10]", "2025-01-01"),  # 9 years old
        ("2015-01-01", "[10-20]", "2025-01-01"),  # 10 years old
        ("2014-12-31", "[10-20]", "2025-01-01"),  # 10 years old
        # Edge cases
        ("1900-01-01", "[120-130]", "2025-01-01"),
        ("2023-12-31", "[0-10]", "2025-01-01"),
        # Invalid formats
        ("invalid-date", None, "2025-01-01"),
        ("", None, "2025-01-01"),
    ],
)
def test_calculate_age_group(birthday, expected_age_group, frozen_date):
    """Test age group calculation with frozen time for deterministic results."""
    with freeze_time(frozen_date):
        assert calculate_age_group(birthday) == expected_age_group


@pytest.mark.parametrize(
    "birthday,frozen_date",
    [
        ("2025-01-02", "2025-01-01"),  # 1 day in future
        ("2026-01-01", "2025-01-01"),  # 1 year in future
        ("2030-01-01", "2025-01-01"),  # 5 years in future
    ],
)
def test_calculate_age_group_future_birthday(birthday, frozen_date):
    """Test that future birthdays raise ValueError."""
    with freeze_time(frozen_date), pytest.raises(ValueError, match=f"Birthday {birthday} is in the future"):
        calculate_age_group(birthday)


def test_calculate_age_group_fails_with_none():
    """Test that None birthday raises TypeError."""
    with pytest.raises(TypeError):
        calculate_age_group(None)


# Test data for extract_email_domain
@pytest.mark.parametrize(
    "email,expected_domain",
    [
        # Valid email formats
        ("john.doe@example.com", "example.com"),
        ("user@sub.domain.com", "sub.domain.com"),
        ("user123@example.co.uk", "example.co.uk"),
        ("email@subdomain.example.museum", "subdomain.example.museum"),
        ("user+filter@gmail.com", "gmail.com"),
        ("user.name@example.com", "example.com"),
        # Invalid email formats
        ("test@localhost", None),
        ("user@[123.123.123.123]", None),
        ("@domain.com", None),  # Missing local part
        ("user@@domain.com", None),  # Double @
        ("user@", None),  # Missing domain
        ("user@.", None),  # Invalid domain
        ("user@.com", None),  # Invalid domain
        ("user@..com", None),  # Double dot
        ("user@domain.", None),  # Trailing dot
        (".user@domain.com", None),  # leading dot in local part
        ("no-at-symbol", None),
        ("", None),
        (None, None),
    ],
)
def test_extract_email_domain(email, expected_domain):
    """Test email domain extraction for various email formats."""
    assert extract_email_domain(email) == expected_domain


# Test data for anonymize_person
@pytest.mark.parametrize(
    # fmt: off
    "person_data,expected_anonymized,frozen_date",
    [
        (
            Person(id="person123", firstname="John", lastname="Doe", email="john.doe@example.com", phone="1234567890", birthday="1990-01-01", gender="M", website="https://example.com", image="https://example.com/image.jpg", address=SAMPLE_ADDRESS),
            AnonymizedPerson(age_group="[30-40]", email_domain="example.com", country="USA", city="New York"),
            "2025-01-01",
        ),
        # Test with empty values
        (
            Person(id="empty123", firstname="", lastname="", email="@example.com", phone="", birthday="invalid-date", gender="", website="", image="", address=EMPTY_ADDRESS),
            AnonymizedPerson(age_group=None, email_domain=None, country="", city=""),
            "2025-01-01",
        ),
        # Test with missing email domain
        (
            Person(id="person456", firstname="John", lastname="Doe", email="no-domain", phone="1234567890", birthday="1990-01-01", gender="F", website="https://example.com", image="https://example.com/image.jpg", address=SAMPLE_ADDRESS),
            AnonymizedPerson(age_group="[30-40]", email_domain=None, country="USA", city="New York"),
            "2025-01-01",
        ),
        # Test with different birth year
        (
            Person(id="person789", firstname="John", lastname="Doe", email="john.doe@example.com", phone="1234567890", birthday="1980-01-01", gender="M", website="https://example.com", image="https://example.com/image.jpg", address=SAMPLE_ADDRESS),
            AnonymizedPerson(age_group="[40-50]", email_domain="example.com", country="USA", city="New York"),
            "2025-01-01",
        ),
        # Test with future birth date
        (
            Person(id="person101", firstname="John", lastname="Doe", email="john.doe@example.com", phone="1234567890", birthday="2025-01-01", gender="F", website="https://example.com", image="https://example.com/image.jpg", address=SAMPLE_ADDRESS),
            AnonymizedPerson(age_group="[0-10]", email_domain="example.com", country="USA", city="New York"),
            "2025-01-01",
        ),
        # fmt: on
    ]
    ,
)
def test_anonymize_person(person_data, expected_anonymized, frozen_date):
    """Test complete person anonymization with frozen time for deterministic results."""
    with freeze_time(frozen_date):
        anonymized = anonymize_person(person_data)
        assert anonymized.age_group == expected_anonymized.age_group
        assert anonymized.email_domain == expected_anonymized.email_domain
        assert anonymized.country == expected_anonymized.country
        assert anonymized.city == expected_anonymized.city
