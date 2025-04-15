"""Tests for database operations."""

import os
import tempfile
from pathlib import Path

import pytest

from src.database import AnonymizedPerson, create_db, get_db_url


def test_get_db_url():
    dbpath = Path("data/anonymized_data.db")
    assert get_db_url(dbpath) == "sqlite:///data/anonymized_data.db"


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()
    yield temp_db.name
    try:
        os.unlink(temp_db.name)
    except OSError:
        pass


@pytest.fixture
def db(temp_db_path):
    """Create a new database instance for each test."""
    db = create_db(f"sqlite:///{temp_db_path}")
    yield db
    db.engine.dispose()


def test_database_creation(temp_db_path):
    """Test that database file is created."""
    db = create_db(f"sqlite:///{temp_db_path}")
    assert os.path.exists(temp_db_path)
    # Verify table exists
    with db.transaction() as session:
        assert session.query(AnonymizedPerson).first() is None
    db.engine.dispose()


def test_write_and_read_persons(db) -> None:
    """Test writing and reading persons from the database."""
    # Create test data
    persons = [
        AnonymizedPerson(
            age_group="[20-30]",
            email_domain="example.com",
            country="USA",
            city="New York",
        ),
        AnonymizedPerson(
            age_group="[30-40]",
            email_domain="gmail.com",
            country="UK",
            city="London",
        ),
    ]

    # Write persons
    db.write_persons(persons)

    # Read and verify
    retrieved_persons = list(db.read_persons())
    assert len(retrieved_persons) == 2

    # Verify first person
    assert retrieved_persons[0].age_group == "[20-30]"
    assert retrieved_persons[0].email_domain == "example.com"
    assert retrieved_persons[0].country == "USA"
    assert retrieved_persons[0].city == "New York"

    # Verify second person
    assert retrieved_persons[1].age_group == "[30-40]"
    assert retrieved_persons[1].email_domain == "gmail.com"
    assert retrieved_persons[1].country == "UK"
    assert retrieved_persons[1].city == "London"


def test_get_person(db) -> None:
    """Test retrieving a single person by ID."""
    # Create and save a person
    person = AnonymizedPerson(
        age_group="[20-30]",
        email_domain="example.com",
        country="USA",
        city="New York",
    )
    db.write_persons([person])

    # Retrieve and verify
    retrieved_person = db.get_person(1)
    assert retrieved_person is not None
    assert retrieved_person.age_group == "[20-30]"
    assert retrieved_person.email_domain == "example.com"
    assert retrieved_person.country == "USA"
    assert retrieved_person.city == "New York"


def test_get_nonexistent_person(db) -> None:
    """Test retrieving a nonexistent person."""
    assert db.get_person(999) is None


def test_transaction_rollback(db) -> None:
    """Test transaction rollback on error."""
    # Create a person
    person = AnonymizedPerson(
        age_group="[20-30]",
        email_domain="example.com",
        country="USA",
        city="New York",
    )

    # Try to write with an error
    with pytest.raises(Exception):
        with db.transaction() as session:
            session.add(person)
            raise Exception("Test error")

    # Verify person was not saved
    assert db.get_person(1) is None
