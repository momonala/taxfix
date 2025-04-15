"""Database operations using SQLAlchemy ORM."""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()


def get_db_url(dbpath: Path) -> str:
    return f"sqlite:///{dbpath}"


class AnonymizedPerson(Base):
    """SQLAlchemy model for anonymized person data."""

    __tablename__ = "anonymized_persons"

    id = Column(Integer, primary_key=True)
    age_group = Column(String)
    email_domain = Column(String)
    country = Column(String)
    city = Column(String)


class Database:
    """Handles database operations using SQLAlchemy."""

    def __init__(self, db_url: str = "sqlite:///anonymized_data.db"):
        """Initialize database connection."""
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """Context manager for database transactions.
        Automatically commits or rolls back on exception.

        Yields:
            SQLAlchemy session

        Example:
            with db.transaction() as session:
                # Do database operations
                session.add(person)
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def write_persons(self, persons: list[AnonymizedPerson]) -> None:
        """Write a list of anonymized persons to the database."""
        with self.transaction() as session:
            session.add_all(persons)
        logger.info(f"Wrote {len(persons)} persons to the database")

    def read_persons(self) -> list[AnonymizedPerson]:
        """Read all anonymized persons from the database."""
        with self.transaction() as session:
            return session.query(AnonymizedPerson).all()

    def get_person(self, person_id: int) -> AnonymizedPerson | None:
        """Get a single person by ID."""
        with self.transaction() as session:
            return session.query(AnonymizedPerson).get(person_id)


def create_db(db_url: str = "sqlite:///anonymized_data.db") -> Database:
    """Create and initialize a new database instance."""
    db = Database(db_url)
    return db
