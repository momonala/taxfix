"""Tests for report generation queries."""

import os
import tempfile
from pathlib import Path

import pytest
from freezegun import freeze_time
from sqlalchemy import create_engine

from src.database import AnonymizedPerson, Base, Database
from src.generate_report import (
    calculate_gmail_users_germany_percentage,
    get_top_gmail_countries,
    count_gmail_users_over_60,
    generate_report,
)


@pytest.fixture
def db():
    """Create a test database using a temporary file."""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()
    db_url = f"sqlite:///{temp_db.name}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    database = Database(db_url)
    yield database
    os.unlink(temp_db.name)


@pytest.fixture
def db_path():
    """Create a temporary database file and return its path."""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()
    yield Path(temp_db.name)
    os.unlink(temp_db.name)


@pytest.fixture
def sample_data(db):
    """Create sample data for testing."""
    test_data = [
        # German Gmail users
        AnonymizedPerson(id=1, email_domain="gmail.com", country="Germany", age_group="[30-40]"),
        AnonymizedPerson(id=2, email_domain="gmail.com", country="Germany", age_group="[60-70]"),
        # German non-Gmail users
        AnonymizedPerson(id=3, email_domain="outlook.com", country="Germany", age_group="[20-30]"),
        AnonymizedPerson(id=4, email_domain="yahoo.com", country="Germany", age_group="[40-50]"),
        # Non-German Gmail users
        AnonymizedPerson(id=5, email_domain="gmail.com", country="USA", age_group="[50-60]"),
        AnonymizedPerson(id=6, email_domain="gmail.com", country="USA", age_group="[70-80]"),
        AnonymizedPerson(id=7, email_domain="gmail.com", country="France", age_group="[80-90]"),
        # Other users
        AnonymizedPerson(id=8, email_domain="outlook.com", country="UK", age_group="[90-100]"),
        AnonymizedPerson(id=9, email_domain="yahoo.com", country="Spain", age_group="[40-50]"),
    ]

    with db.transaction() as session:
        for person in test_data:
            session.add(person)
    return test_data


# Tests for calculate_gmail_users_germany_percentage
def test_gmail_germany_percentage(db, sample_data):
    """Test calculation of Gmail usage percentage in Germany."""
    percentage = calculate_gmail_users_germany_percentage(db)
    assert percentage == pytest.approx(50.0)  # 2 Gmail users out of 4 German users


def test_gmail_germany_percentage_no_germans(db):
    """Test Gmail percentage calculation with no German users."""
    test_data = [
        AnonymizedPerson(id=1, email_domain="gmail.com", country="USA", age_group="[30-40]"),
        AnonymizedPerson(id=2, email_domain="outlook.com", country="UK", age_group="[40-50]"),
    ]
    with db.transaction() as session:
        for person in test_data:
            session.add(person)

    percentage = calculate_gmail_users_germany_percentage(db)
    assert percentage == 0.0


def test_gmail_germany_percentage_empty_db(db):
    """Test Gmail percentage calculation with empty database."""
    percentage = calculate_gmail_users_germany_percentage(db)
    assert percentage == 0.0


# Tests for get_top_gmail_countries
def test_top_gmail_countries(db, sample_data):
    """Test getting top countries using Gmail."""
    top_countries = get_top_gmail_countries(db)
    assert len(top_countries) == 3
    assert ("USA", 2) in top_countries
    assert ("Germany", 2) in top_countries
    assert ("France", 1) in top_countries


def test_top_gmail_countries_with_ties(db):
    """Test getting top countries with tied counts."""
    test_data = [
        # Two countries tied for first (3 users)
        AnonymizedPerson(id=1, email_domain="gmail.com", country="USA", age_group="[30-40]"),
        AnonymizedPerson(id=2, email_domain="gmail.com", country="USA", age_group="[40-50]"),
        AnonymizedPerson(id=3, email_domain="gmail.com", country="USA", age_group="[50-60]"),
        AnonymizedPerson(id=4, email_domain="gmail.com", country="Germany", age_group="[30-40]"),
        AnonymizedPerson(id=5, email_domain="gmail.com", country="Germany", age_group="[40-50]"),
        AnonymizedPerson(id=6, email_domain="gmail.com", country="Germany", age_group="[50-60]"),
        # Two countries tied for second (2 users)
        AnonymizedPerson(id=7, email_domain="gmail.com", country="France", age_group="[60-70]"),
        AnonymizedPerson(id=8, email_domain="gmail.com", country="France", age_group="[70-80]"),
        AnonymizedPerson(id=9, email_domain="gmail.com", country="UK", age_group="[60-70]"),
        AnonymizedPerson(id=10, email_domain="gmail.com", country="UK", age_group="[70-80]"),
        # One country with 1 user
        AnonymizedPerson(id=11, email_domain="gmail.com", country="Spain", age_group="[80-90]"),
    ]
    with db.transaction() as session:
        for person in test_data:
            session.add(person)

    top_countries = get_top_gmail_countries(db)
    
    # Should include all countries tied for positions within top 3
    assert len(top_countries) == 4  # USA, Germany (tied for 1st), France, UK (tied for 2nd)
    
    # Verify counts
    country_dict = dict(top_countries)
    assert country_dict["USA"] == 3
    assert country_dict["Germany"] == 3
    assert country_dict["France"] == 2
    assert country_dict["UK"] == 2
    # Spain should not be included as it's not tied with any top 3 position
    assert "Spain" not in country_dict


def test_top_gmail_countries_all_tied(db):
    """Test getting top countries when all have the same count."""
    test_data = [
        # All countries have exactly 2 users
        AnonymizedPerson(id=1, email_domain="gmail.com", country="USA", age_group="[30-40]"),
        AnonymizedPerson(id=2, email_domain="gmail.com", country="USA", age_group="[40-50]"),
        AnonymizedPerson(id=3, email_domain="gmail.com", country="Germany", age_group="[50-60]"),
        AnonymizedPerson(id=4, email_domain="gmail.com", country="Germany", age_group="[60-70]"),
        AnonymizedPerson(id=5, email_domain="gmail.com", country="France", age_group="[70-80]"),
        AnonymizedPerson(id=6, email_domain="gmail.com", country="France", age_group="[80-90]"),
        AnonymizedPerson(id=7, email_domain="gmail.com", country="UK", age_group="[30-40]"),
        AnonymizedPerson(id=8, email_domain="gmail.com", country="UK", age_group="[40-50]"),
    ]
    with db.transaction() as session:
        for person in test_data:
            session.add(person)

    top_countries = get_top_gmail_countries(db)
    
    # Should include all countries since they're all tied
    assert len(top_countries) == 4
    assert all(count == 2 for _, count in top_countries)
    countries = {country for country, _ in top_countries}
    assert countries == {"USA", "Germany", "France", "UK"}


def test_top_gmail_countries_with_custom_limit(db):
    """Test getting top countries with a custom limit and ties."""
    test_data = [
        # First place (3 users)
        AnonymizedPerson(id=1, email_domain="gmail.com", country="USA", age_group="[30-40]"),
        AnonymizedPerson(id=2, email_domain="gmail.com", country="USA", age_group="[40-50]"),
        AnonymizedPerson(id=3, email_domain="gmail.com", country="USA", age_group="[50-60]"),
        # Tied for second (2 users each)
        AnonymizedPerson(id=4, email_domain="gmail.com", country="Germany", age_group="[30-40]"),
        AnonymizedPerson(id=5, email_domain="gmail.com", country="Germany", age_group="[40-50]"),
        AnonymizedPerson(id=6, email_domain="gmail.com", country="France", age_group="[60-70]"),
        AnonymizedPerson(id=7, email_domain="gmail.com", country="France", age_group="[70-80]"),
        # Third place (1 user)
        AnonymizedPerson(id=8, email_domain="gmail.com", country="Spain", age_group="[80-90]"),
    ]
    with db.transaction() as session:
        for person in test_data:
            session.add(person)

    # Request top 2, but should get 3 due to tie
    top_countries = get_top_gmail_countries(db, number_of_countries=2)
    
    assert len(top_countries) == 3  # USA, Germany, France
    
    country_dict = dict(top_countries)
    assert country_dict["USA"] == 3
    assert country_dict["Germany"] == 2
    assert country_dict["France"] == 2
    assert "Spain" not in country_dict


def test_top_gmail_countries_empty_db(db):
    """Test getting top countries with empty database."""
    top_countries = get_top_gmail_countries(db)
    assert top_countries == []


def test_top_gmail_countries_no_gmail_users(db):
    """Test getting top countries when there are no Gmail users."""
    test_data = [
        AnonymizedPerson(id=1, email_domain="outlook.com", country="USA", age_group="[30-40]"),
        AnonymizedPerson(id=2, email_domain="yahoo.com", country="Germany", age_group="[40-50]"),
        AnonymizedPerson(id=3, email_domain="hotmail.com", country="France", age_group="[50-60]"),
    ]
    with db.transaction() as session:
        for person in test_data:
            session.add(person)

    top_countries = get_top_gmail_countries(db)
    assert top_countries == []


def test_count_gmail_users_over_60(db, sample_data):
    """Test counting Gmail users over 60."""
    count = count_gmail_users_over_60(db)
    assert count == 3


def test_count_gmail_users_over_60_edge_cases(db):
    """Test counting Gmail users over 60 with edge cases."""
    test_data = [
        AnonymizedPerson(id=1, email_domain="gmail.com", country="USA", age_group="[60-70]"),  # Should count
        AnonymizedPerson(id=2, email_domain="gmail.com", country="USA", age_group="[50-60]"),  # Should not count
        AnonymizedPerson(id=3, email_domain="outlook.com", country="USA", age_group="[70-80]"),  # Wrong email
        AnonymizedPerson(id=4, email_domain="gmail.com", country="USA", age_group="[90-100]"),  # Should count
    ]
    with db.transaction() as session:
        for person in test_data:
            session.add(person)

    count = count_gmail_users_over_60(db)
    assert count == 2  # Only [60-70] and [90-100] Gmail users


@pytest.mark.parametrize(
    "test_data,expected_count",
    [
        ([], 0),  # Empty database
        (
            [  # Only under-60 users
                AnonymizedPerson(id=1, email_domain="gmail.com", country="USA", age_group="[20-30]"),
                AnonymizedPerson(id=2, email_domain="gmail.com", country="USA", age_group="[50-60]"),
            ],
            0,
        ),
        (
            [  # Only non-Gmail users over 60
                AnonymizedPerson(id=1, email_domain="outlook.com", country="USA", age_group="[60-70]"),
                AnonymizedPerson(id=2, email_domain="yahoo.com", country="USA", age_group="[70-80]"),
            ],
            0,
        ),
    ],
)
def test_count_gmail_users_over_60_zero_cases(db, test_data, expected_count):
    """Test cases where no Gmail users over 60 exist."""
    with db.transaction() as session:
        for person in test_data:
            session.add(person)

    count = count_gmail_users_over_60(db)
    assert count == expected_count
