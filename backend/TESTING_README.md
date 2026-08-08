# Backend Testing Documentation

## Overview

This document describes the testing infrastructure for the E-Career backend API.

## Testing Framework

- **pytest**: Python testing framework
- **pytest-django**: Django integration for pytest
- **pytest-cov**: Coverage reporting
- **factory-boy**: Test data generation

## Test Structure

```
backend/
├── tests/
│   ├── conftest.py          # Shared fixtures and configuration
│   ├── factories.py         # Factory Boy factories
│   ├── test_integration.py  # End-to-end integration tests
│   └── unit/                # Unit tests by app
└── apps/
    ├── accounts/
    │   └── tests/
    │       └── test_auth.py
    ├── career/
    │   └── tests/
    │       └── test_api.py
    ├── interviews/
    │   └── tests/
    │       └── test_api.py
    ├── jobs/
    │   └── tests/
    │       ├── test_models.py
    │       └── test_api.py
    ├── rashid/
    │   └── tests/
    │       └── test_api.py
    └── ...
```

## Running Tests

### Run all tests
```bash
cd backend
pytest
```

### Run tests with coverage
```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

### Run specific app tests
```bash
pytest apps/jobs/tests/
pytest apps/accounts/tests/
pytest apps/career/tests/
pytest apps/rashid/tests/
pytest apps/interviews/tests/
```

### Run specific test file
```bash
pytest apps/jobs/tests/test_api.py
```

### Run specific test class
```bash
pytest apps/jobs/tests/test_api.py::TestJobAPI
```

### Run specific test
```bash
pytest apps/jobs/tests/test_api.py::TestJobAPI::test_list_jobs_anonymous
```

### Run tests with verbose output
```bash
pytest -v
```

### Run tests with pdb (debug)
```bash
pytest -x --pdb
```

## Test Fixtures

### User Fixtures
- `api_client`: Unauthenticated API client
- `user`: Regular user fixture
- `admin_user`: Admin user fixture
- `auth_client`: API client authenticated as regular user
- `admin_client`: API client authenticated as admin user

### Job Fixtures
- `company`: Test company
- `source`: Test job source
- `tag`: Test skill tag
- `job`: Active job listing
- `inactive_job`: Archived job listing

### Mock Fixtures
- `mock_bedrock_client`: Mock AWS Bedrock AI client
- `mock_typesense_client`: Mock Typesense search client
- `mock_qdrant_client`: Mock Qdrant vector database
- `mock_s3_client`: Mock AWS S3 client
- `mock_email_backend`: Mock email sending
- `mock_redis_client`: Mock Redis client
- `mock_celery_task`: Mock Celery task

## Writing Tests

### Basic Test Structure
```python
import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
class TestExampleAPI:
    def test_example_endpoint(self, api_client):
        url = reverse("example:endpoint")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
```

### Using Fixtures
```python
@pytest.mark.django_db
class TestJobAPI:
    def test_list_jobs(self, api_client, job):
        url = reverse("jobs:job-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) >= 1
```

### Testing with Authentication
```python
@pytest.mark.django_db
class TestProtectedAPI:
    def test_protected_endpoint(self, auth_client):
        url = reverse("protected:endpoint")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
```

### Testing with Mocks
```python
@pytest.mark.django_db
class TestAIEndpoint:
    def test_ai_response(self, auth_client, mock_bedrock_client):
        url = reverse("ai:endpoint")
        response = auth_client.post(url, {"prompt": "test"})
        assert response.status_code == status.HTTP_200_OK
        mock_bedrock_client.generate_text.assert_called_once()
```

## Coverage

Coverage reports are automatically generated. To view the HTML report:
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## CI/CD Integration

Tests are run on every push and pull request. The CI pipeline:
1. Runs all tests with coverage
2. Fails if coverage drops below threshold
3. Generates coverage report for review

## Best Practices

1. **Test naming**: Use descriptive names like `test_<what>_when_<condition>`
2. **Test isolation**: Each test should be independent
3. **Use fixtures**: Leverage conftest.py fixtures for common data
4. **Mock external services**: Use mock fixtures for AI, search, and storage
5. **Test edge cases**: Include error handling and edge cases
6. **Keep tests fast**: Use database fixtures efficiently
7. **Test public API**: Focus on testing views and serializers

## Troubleshooting

### Database errors
```bash
# Reset database
python manage.py migrate --run-syncdb

# Or use pytest-django's database reset
pytest --create-db
```

### Slow tests
```bash
# Show slowest tests
pytest --durations=10
```

### Debugging
```bash
# Stop at first failure
pytest -x

# Drop into debugger
pytest --pdb

# Show print statements
pytest -s