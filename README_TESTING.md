# 🧪 Testing Guide

## Quick Start

### Install Dependencies

```bash
# Install Python test dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium firefox

# Install Lighthouse (requires Node.js)
npm install -g lighthouse
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m e2e              # E2E tests only
pytest -m lighthouse       # Lighthouse tests only

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_pdf_normalizer.py -v
```

## Test Structure

```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── test_pdf_normalizer.py
│   └── test_validation.py
├── integration/       # Integration tests (require database)
│   └── test_api_endpoints.py
├── e2e/              # End-to-end tests (require browser)
│   └── test_user_workflow.py
├── lighthouse/       # Performance tests
│   └── test_performance.py
└── conftest.py      # Shared fixtures
```

## Test Categories

### Unit Tests
- **Purpose**: Test individual functions in isolation
- **Speed**: Fast (< 1 second)
- **Dependencies**: None (mocked)
- **Examples**: PDF normalizer, validation logic

### Integration Tests
- **Purpose**: Test API endpoints and database interactions
- **Speed**: Medium (1-5 seconds)
- **Dependencies**: Test database
- **Examples**: File upload, invoice creation

### E2E Tests
- **Purpose**: Test complete user workflows
- **Speed**: Slow (5-30 seconds)
- **Dependencies**: Running application, browser
- **Examples**: Signup → Login → Upload → Validate

### Lighthouse Tests
- **Purpose**: Performance, accessibility, SEO
- **Speed**: Very slow (30-60 seconds)
- **Dependencies**: Running application, Lighthouse CLI
- **Examples**: Page load times, accessibility scores

## Running Tests in CI/CD

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: playwright install chromium
      - run: pytest --cov=app --cov-report=xml
```

## Coverage Goals

- **Critical Components**: 100% coverage
  - PDF normalizer
  - Validation logic
  - Account number extraction
  
- **Important Components**: 80%+ coverage
  - API endpoints
  - File processing
  - Database operations

- **Overall**: 80%+ coverage

## Debugging Tests

```bash
# Run with verbose output
pytest -v -s

# Run specific test
pytest tests/unit/test_pdf_normalizer.py::TestPDFNormalizer::test_account_number_extraction -v

# Run with debugger
pytest --pdb

# Show coverage gaps
pytest --cov=app --cov-report=term-missing
```

## Test Data

Test data is created using fixtures in `conftest.py`:
- Test database (SQLite in-memory for unit tests)
- Test users and tenants
- Sample invoice data
- Mock PDF extraction data

## Best Practices

1. **Isolation**: Each test should be independent
2. **Speed**: Unit tests should be fast (< 1s)
3. **Clarity**: Test names should describe what they test
4. **Coverage**: Aim for high coverage on critical paths
5. **Maintenance**: Keep tests updated with code changes

