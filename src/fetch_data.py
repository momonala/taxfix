"""Script to fetch and validate API response and extract person data."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

MAX_API_QUANTITY = 1000  # defined by the Faker API
MAX_WORKERS = 10  # number of concurrent threads


@dataclass
class Address:
    """Address data from the API."""

    id: int
    street: str
    streetName: str
    buildingNumber: str
    city: str
    zipcode: str
    country: str
    country_code: str
    latitude: float
    longitude: float


@dataclass
class Person:
    """Person data from the API."""

    id: int
    firstname: str
    lastname: str
    email: str
    phone: str
    birthday: str
    gender: str
    address: Address
    website: str
    image: str


def _validate_person(data: dict[str, Any]) -> Person | None:
    """Validate and create a Person from dictionary data.

    Args:
        data: Raw person dictionary from API

    Returns:
        Person object if valid, None if invalid
    """
    try:
        # Validate birthday format, Address first
        datetime.strptime(data["birthday"], "%Y-%m-%d")
        address = Address(**data["address"])

        # Create Person (will raise KeyError if missing fields)
        return Person(**{**data, "address": address})
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Invalid person data: {e}")
        return None


def validate_response(response_data: dict[str, Any]) -> list[Person]:
    """Validate API response and extract person data.

    This function performs hierarchical validation of the API response:
    1. Validates response status is "OK"
    2. Validates data field is a list
    3. For each person in the data:
        - Validates all required Person fields exist (id, firstname, lastname, etc.)
        - Validates birthday format (YYYY-MM-DD)
        - Validates all required Address fields exist (id, street, city, etc.)
        - Validates field types via dataclasss constructor (e.g., id is int, latitude is float)

    If any validation fails at any level:
    - Response status not "OK" -> returns empty list
    - Data field not a list -> returns empty list
    - Missing Person field -> skips that person
    - Invalid birthday format -> skips that person
    - Missing Address field -> skips that person
    - Invalid field type -> skips that person

    Args:
        response_data: Raw API response dictionary containing:
            - status: str ("OK" or error status)
            - code: int (HTTP status code)
            - total: int (total number of records)
            - data: list[dict] (list of person dictionaries)

    Returns:
        List of valid Person objects. Empty list if response invalid or no valid persons.
    """
    if response_data.get("status") != "OK":
        logger.error(f"API returned error status: {response_data.get('status')}")
        return []

    persons = response_data.get("data", [])
    if not isinstance(persons, list):
        logger.error("API returned invalid data format")
        return []

    # Validate each person
    valid_persons = []
    for person_data in persons:
        if person := _validate_person(person_data):
            valid_persons.append(person)
        else:
            logger.warning("Skipping invalid person data")

    return valid_persons


def _create_session() -> requests.Session:
    """Create a requests session with retry policy for 5xx errors and rate limits."""
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _fetch_batch(session: requests.Session, batch_num: int, batch_size: int) -> list[Person]:
    """Fetch a single batch of persons from the Faker API.

    Args:
        session: Requests session with retry policy
        batch_num: The batch number (for logging)
        batch_size: Number of persons to fetch in this batch

    Returns:
        list of Person objects from the API
    """
    base_url = "https://fakerapi.it/api/v2/persons"
    params = {"_quantity": batch_size, "_birthday_start": "1900-01-01"}

    try:
        logger.info(f"Batch {batch_num}: Fetching {batch_size} persons")
        response = session.get(base_url, params=params, timeout=30)
        response.raise_for_status()

        valid_persons = validate_response(response.json())
        logger.info(f"Batch {batch_num}: Successfully fetched {len(valid_persons)} valid persons")
        return valid_persons

    except requests.exceptions.RequestException as e:
        logger.error(f"Batch {batch_num}: Error fetching data from Faker API: {e}")
        raise
    except Exception as e:
        logger.error(f"Batch {batch_num}: Unexpected error: {e}")
        raise


def fetch_persons(quantity: int) -> list[Person]:
    """Fetch person data from the Faker API using parallel requests.

    Args:
        quantity: Number of persons to fetch

    Returns:
        list of Person objects from the API
    """
    all_persons = []
    valid_persons_count = 0

    # Calculate number of batches needed
    num_batches = (quantity + MAX_API_QUANTITY - 1) // MAX_API_QUANTITY
    logger.info(f"Making {num_batches} parallel requests to fetch {quantity} persons")

    # Execute requests in parallel
    session = _create_session()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i in range(num_batches):
            batch_size = min(MAX_API_QUANTITY, quantity - (i * MAX_API_QUANTITY))
            future = executor.submit(_fetch_batch, session, i + 1, batch_size)
            futures.append(future)

        # Process completed futures as they come in
        for future in as_completed(futures):
            try:
                batch_persons = future.result()
                all_persons.extend(batch_persons)
                valid_persons_count += len(batch_persons)
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")
                continue  # Try to process remaining batches

    logger.info(f"Total valid persons fetched: {valid_persons_count}")
    return all_persons
