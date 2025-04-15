"""Script to generate anonymized data statistics report."""

import logging
from pathlib import Path

from sqlalchemy import func

from src.database import AnonymizedPerson, Database, create_db, get_db_url

logger = logging.getLogger(__name__)


def calculate_gmail_users_germany_percentage(db: Database) -> float:
    """Calculate percentage of users in Germany using Gmail."""
    with db.transaction() as session:
        total_users_germany = session.query(AnonymizedPerson).filter(AnonymizedPerson.country == "Germany").count()
        if total_users_germany == 0:
            return 0.0
        gmail_users_germany = (
            session.query(AnonymizedPerson)
            .filter(AnonymizedPerson.country == "Germany", AnonymizedPerson.email_domain == "gmail.com")
            .count()
        )

        return (gmail_users_germany / total_users_germany) * 100


def get_top_gmail_countries(db: Database, number_of_countries: int = 3) -> list[tuple[str, int]]:
    """Get top countries using Gmail, including ties.
    
    Args:
        db: Database instance
        number_of_countries: Minimum number of countries to return (more will be included if tied)
        
    Returns:
        List of (country, count) tuples, including all countries tied for the last position
    """
    with db.transaction() as session:
        country_counts = (
            session.query(AnonymizedPerson.country, func.count(AnonymizedPerson.id).label("count"))
            .filter(AnonymizedPerson.email_domain == "gmail.com")
            .group_by(AnonymizedPerson.country)
            .order_by(func.count(AnonymizedPerson.id).desc())
            .all()
        )

        if not country_counts:
            return []

        sorted_country_counts = sorted(country_counts, key=lambda x: x[1], reverse=True)
        
        # If we have fewer countries than requested, return all
        if len(sorted_country_counts) <= number_of_countries:
            return sorted_country_counts
            
        # Get the count of the last country that would be included
        cutoff_count = sorted_country_counts[number_of_countries - 1][1]
        
        # Include all countries that have at least this count
        return [x for x in sorted_country_counts if x[1] >= cutoff_count]


def count_gmail_users_over_60(db: Database) -> int:
    """Count users over 60 using Gmail."""
    with db.transaction() as session:
        return (
            session.query(AnonymizedPerson)
            .filter(
                AnonymizedPerson.email_domain == "gmail.com",
                AnonymizedPerson.age_group.in_(["[60-70]", "[70-80]", "[80-90]", "[90-100]"]),
            )
            .count()
        )


def generate_report(db_path: Path):
    """Generate and display the statistics report."""
    db = create_db(get_db_url(db_path))
    logger.info(f"Database initialized at {db_path}")

    gmail_users_germany_pct = calculate_gmail_users_germany_percentage(db)
    top_gmail_countries = get_top_gmail_countries(db)
    gmail_over_60 = count_gmail_users_over_60(db)

    report = f"""
Anonymized Data Statistics Report
================================

1. Percentage of users in Germany using Gmail:
   {gmail_users_germany_pct:.2f}%

2. Top countries using Gmail (including ties):
"""
    for country, count in top_gmail_countries:
        report += f"   - {country}: {count} users\n"

    report += f"""
3. Number of users over 60 using Gmail:
   {gmail_over_60} users
"""

    print(report)
    logger.info("Report generated successfully")
