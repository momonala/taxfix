"""Tests for fetch_data module."""

import pytest

from src.fetch_data import Person, validate_response


@pytest.mark.parametrize(
    "test_id,response_data,expected_count",
    [
        (
            "valid_single_person",
            {
                "status": "OK",
                "code": 200,
                "total": 1,
                "data": [
                    {
                        "id": 1,
                        "firstname": "John",
                        "lastname": "Doe",
                        "email": "john@example.com",
                        "phone": "+1234567890",
                        "birthday": "1990-01-01",
                        "gender": "male",
                        "website": "http://example.com",
                        "image": "http://example.com/image.jpg",
                        "address": {
                            "id": 1,
                            "street": "123 Main St",
                            "streetName": "Main St",
                            "buildingNumber": "123",
                            "city": "Anytown",
                            "zipcode": "12345",
                            "country": "USA",
                            "country_code": "US",
                            "latitude": 42.123,
                            "longitude": -71.123,
                        },
                    }
                ],
            },
            1,
        ),
        ("invalid_status", {"status": "ERROR", "code": 500, "total": 0, "data": []}, 0),
        (
            "missing_required_person_field",
            {
                "status": "OK",
                "code": 200,
                "total": 1,
                "data": [
                    {
                        "id": 1,
                        "firstname": "John",
                        # missing lastname
                        "email": "john@example.com",
                        "phone": "+1234567890",
                        "birthday": "1990-01-01",
                        "gender": "male",
                        "website": "http://example.com",
                        "image": "http://example.com/image.jpg",
                        "address": {
                            "id": 1,
                            "street": "123 Main St",
                            "streetName": "Main St",
                            "buildingNumber": "123",
                            "city": "Anytown",
                            "zipcode": "12345",
                            "country": "USA",
                            "country_code": "US",
                            "latitude": 42.123,
                            "longitude": -71.123,
                        },
                    }
                ],
            },
            0,
        ),
        (
            "missing_required_address_field",
            {
                "status": "OK",
                "code": 200,
                "total": 1,
                "data": [
                    {
                        "id": 1,
                        "firstname": "John",
                        "lastname": "Doe",
                        "email": "john@example.com",
                        "phone": "+1234567890",
                        "birthday": "1990-01-01",
                        "gender": "male",
                        "website": "http://example.com",
                        "image": "http://example.com/image.jpg",
                        "address": {
                            "id": 1,
                            "street": "123 Main St",
                            "streetName": "Main St",
                            "buildingNumber": "123",
                            # missing city
                            "zipcode": "12345",
                            "country": "USA",
                            "country_code": "US",
                            "latitude": 42.123,
                            "longitude": -71.123,
                        },
                    }
                ],
            },
            0,
        ),
        (
            "invalid_birthday_format",
            {
                "status": "OK",
                "code": 200,
                "total": 1,
                "data": [
                    {
                        "id": 1,
                        "firstname": "John",
                        "lastname": "Doe",
                        "email": "john@example.com",
                        "phone": "+1234567890",
                        "birthday": "01-01-1990",  # wrong format
                        "gender": "male",
                        "website": "http://example.com",
                        "image": "http://example.com/image.jpg",
                        "address": {
                            "id": 1,
                            "street": "123 Main St",
                            "streetName": "Main St",
                            "buildingNumber": "123",
                            "city": "Anytown",
                            "zipcode": "12345",
                            "country": "USA",
                            "country_code": "US",
                            "latitude": 42.123,
                            "longitude": -71.123,
                        },
                    }
                ],
            },
            0,
        ),
        ("invalid_data_type", {"status": "OK", "code": 200, "total": 1, "data": "not a list"}, 0),  # wrong type
        (
            "multiple_valid_persons",
            {
                "status": "OK",
                "code": 200,
                "total": 2,
                "data": [
                    {
                        "id": 1,
                        "firstname": "John",
                        "lastname": "Doe",
                        "email": "john@example.com",
                        "phone": "+1234567890",
                        "birthday": "1990-01-01",
                        "gender": "male",
                        "website": "http://example.com",
                        "image": "http://example.com/image.jpg",
                        "address": {
                            "id": 1,
                            "street": "123 Main St",
                            "streetName": "Main St",
                            "buildingNumber": "123",
                            "city": "Anytown",
                            "zipcode": "12345",
                            "country": "USA",
                            "country_code": "US",
                            "latitude": 42.123,
                            "longitude": -71.123,
                        },
                    },
                    {
                        "id": 2,
                        "firstname": "Jane",
                        "lastname": "Doe",
                        "email": "jane@example.com",
                        "phone": "+1234567891",
                        "birthday": "1991-02-02",
                        "gender": "female",
                        "website": "http://example2.com",
                        "image": "http://example.com/image2.jpg",
                        "address": {
                            "id": 2,
                            "street": "456 Oak St",
                            "streetName": "Oak St",
                            "buildingNumber": "456",
                            "city": "Othertown",
                            "zipcode": "67890",
                            "country": "Canada",
                            "country_code": "CA",
                            "latitude": 45.123,
                            "longitude": -75.123,
                        },
                    },
                ],
            },
            2,
        ),
    ],
)
def test_validate_response(test_id: str, response_data: dict, expected_count: int):
    """Test validate_response function with various test cases."""
    result = validate_response(response_data)

    assert len(result) == expected_count

    if expected_count > 0:
        # Verify all results are Person objects
        assert all(isinstance(person, Person) for person in result)

        # For multiple persons test case, verify specific fields
        if test_id == "multiple_valid_persons":
            assert result[0].firstname == "John"
            assert result[1].firstname == "Jane"
            assert result[0].address.country == "USA"
            assert result[1].address.country == "Canada"
