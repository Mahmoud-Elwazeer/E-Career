# Testing Guide

## Overview

This document describes the testing approach for the E-Career project.

## Test Suite Structure

```
backend/
├── apps/
│   ├── jobs/
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_models.py
│   ├── employers/
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_models.py
│   ├── profiles/
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_services.py
│   ├── verification/
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_engine.py
│   └── career/
│       └── tests/
│           ├── __init__.py
│           └── test_scoring.py
```

## Running Tests

### Run All Tests
```bash
cd backend
python manage.py test
```

### Run Tests for a Specific App
```bash
python manage.py test jobs.tests
python manage.py test employers.tests
python manage.py test profiles.tests
python manage.py test verification.tests
python manage.py test career.tests
```

### Run Tests with Verbose Output
```bash
python manage.py test --verbosity=2
```

### Run Tests with Coverage
```bash
pip install coverage
coverage run manage.py test
coverage report
coverage html
```

## Test Types

### 1. Model Tests
Tests for Django models including:
- Field validation
- Model methods
- Managers
- Signals

### 2. Service Tests
Tests for business logic in service classes:
- Matching algorithm
- CV parsing
- Skill extraction

### 3. API Tests
Tests for REST API endpoints:
- Authentication
- Authorization
- Request/response validation
- Error handling

### 4. Integration Tests
Tests for end-to-end workflows:
- User registration and profile completion
- Job search and application
- AI-powered matching

## Test Standards

### Naming Conventions
- Test files: `test_*.py`
- Test classes: `*Test`
- Test methods: `test_*`

### Test Quality
- Each test should test one thing
- Tests should be independent and order-independent
- Use fixtures for test data
- Mock external dependencies

### Coverage Targets
- Minimum: 60% coverage
- Target: 80% coverage
- Critical paths: 100% coverage

## CI/CD Integration

Tests are run automatically on:
- Pull requests
- Merges to main branch
- Scheduled runs (daily)

## Adding New Tests

1. Create test file in `apps/<app_name>/tests/`
2. Import necessary modules
3. Create test class extending `TestCase`
4. Add test methods with descriptive names
5. Run tests to verify

Example:
```python
from django.test import TestCase
from apps.jobs.models import Job

class JobTest(TestCase):
    def test_job_creation(self):
        # Test job creation
        pass