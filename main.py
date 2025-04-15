"""Main script to fetch, anonymize, and store person data."""

import logging
from pathlib import Path

from src.data_anonymization import anonymize_person
from src.database import create_db, get_db_url
from src.fetch_data import fetch_persons
from src.generate_report import generate_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


DB_PATH = Path("data/anonymized_data.db")


def main():
    """Main function to fetch, anonymize, and store person data."""
    # Create database directory if it doesn't exist
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Initialize database
    db = create_db(get_db_url(DB_PATH))
    logger.info(f"Database initialized at {DB_PATH}")

    # Fetch and anonymize data
    logger.info("Starting data fetch and anonymization")
    persons = fetch_persons(quantity=30000)
    if not persons:
        raise ValueError("No valid person data fetched from API")
    anonymized_persons = [anonymize_person(person) for person in persons]
    logger.info(f"Anonymized {len(anonymized_persons)} persons")

    # Save to database
    logger.info("Saving anonymized data to database")
    db.write_persons(anonymized_persons)
    logger.info("Data successfully saved to database")

    # Generate report
    generate_report(DB_PATH)


if __name__ == "__main__":
    main()
