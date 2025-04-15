# Data Anonymization Project

TaxFix Technical Interview project for querying, anonymizing, storing, and reporting on user data using the Faker API.

For pipeline design, [see here](pipeline.md)

Notes: 
- Max quanitity size from FakerAPI is 1000, so we execute 30 requests with multithreading
- Includes tests (parameterized)
- Uses `SQLAlchemy` as an ORM binding for the `SQLite` DB
- Email validation tests with `email-validator` module
- Uses `Poetry` for dependency management, optionally with `black`, `isort`, and `pytest-coverage`

## Dependencies

- Python 3.11+
- Docker
- Poetry

## Development (local)

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install Dependencies**:
   ```bash
   poetry install
   ```

## 🐳 Docker

### Building and run the image/pipeline

```bash
// build image
docker build -t data-anonymization .

// run pipeline
docker run data-anonymization

// run tests
docker run data-anonymization pytest
```

## 📁 Project Structure

```
.
├── Dockerfile
├── README.md
├── data                       // contains the SQLite Database
│   └── anonymized_data.db
├── main.py                    // main entry point - fetches data from API, parses, anonymizes, stores, and reports
├── poetry.lock                // for installing dependencies
├── pyproject.toml             // for managing dependencies and dev-tools
├── src                        // contains all application code for pipeline
│   ├── data_anonymization.py
│   ├── database.py
│   └── generate_report.py
├── tests                      // tests for data anonymization and database (generate report is not tested)
│   ├── __init__.py
│   ├── test_data_anonymization.py
│   └── test_database.py
```

## ✅ Testing

The project was developed with test-driven-development, so I included my tests as well :)

- `pytest.parameterized` tests for various scenarios
- `freezegun` for consistent date testing
- uses `tempfile`s for proper test resource cleanup (`sqlite` DBs)
- missing test coverage in areas involving real API requests (requires mocking or integration testing), and printing out the report (UI)

```bash
$ pytest

---------- coverage: platform darwin, python 3.12.9-final-0 ----------
Name                        Stmts   Miss  Cover   Missing
---------------------------------------------------------
src/data_anonymization.py      29      0   100%
src/database.py                45      0   100%
src/fetch_data.py             102     42    59%   124-129, 143-160, 172-199
src/generate_report.py         37     11    70%   78-103
---------------------------------------------------------
TOTAL                         213     53    75%
```

## 🔄 CI

To demonstrate what a CI could like like, I also added a GitHub Actions pipeline builds and tests code in Docker containers on every push/PR to main. Uses layer caching for faster builds.
