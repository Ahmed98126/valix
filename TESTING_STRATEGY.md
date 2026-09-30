# 🧪 Comprehensive Testing Strategy

## Overview

This document outlines the complete testing strategy for the Invoice Validator application, including Unit Tests, Integration Tests, E2E Tests, and Lighthouse Performance Testing.

---

## 📋 Testing Stack

### 1. **Unit Tests** - `pytest`
- **Purpose**: Test individual functions and classes in isolation
- **Coverage**: PDF processing, validation logic, data normalization, utilities
- **Location**: `tests/unit/`

### 2. **Integration Tests** - `pytest` + `TestClient`
- **Purpose**: Test API endpoints, database interactions, file uploads
- **Coverage**: FastAPI routes, database operations, PDF extraction pipeline
- **Location**: `tests/integration/`

### 3. **E2E Tests** - `Playwright`
- **Purpose**: Test complete user workflows in real browser
- **Coverage**: User signup, login, invoice upload, validation, filtering
- **Location**: `tests/e2e/`

### 4. **Lighthouse Testing** - `lighthouse` + `playwright`
- **Purpose**: Performance, accessibility, SEO, best practices
- **Coverage**: All major pages
- **Location**: `tests/lighthouse/`

---

## 🎯 Test Coverage Goals

### Critical Areas (100% coverage):
- ✅ PDF extraction and normalization
- ✅ Account number extraction logic
- ✅ Invoice validation logic
- ✅ Duplicate detection
- ✅ Multi-tenant isolation

### Important Areas (80%+ coverage):
- ✅ API endpoints
- ✅ File upload processing
- ✅ Column mapping
- ✅ Date parsing
- ✅ Amount parsing

### Nice to Have (60%+ coverage):
- ✅ UI components
- ✅ Error handling
- ✅ Edge cases

---

## 📁 Test Structure

```
tests/
├── unit/
│   ├── test_pdf_normalizer.py
│   ├── test_pdf_processor.py
│   ├── test_validation.py
│   ├── test_column_mapping.py
│   └── test_utils.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_file_upload.py
│   ├── test_database.py
│   └── test_pdf_processing.py
├── e2e/
│   ├── test_user_workflow.py
│   ├── test_invoice_upload.py
│   ├── test_validation_flow.py
│   └── test_multi_tenant.py
├── lighthouse/
│   ├── lighthouse_config.js
│   └── test_performance.py
├── fixtures/
│   ├── sample_invoices.xlsx
│   ├── sample_pdf.pdf
│   └── test_data.py
└── conftest.py
```

---

## 🚀 Quick Start

### Install Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov playwright
playwright install
npm install -g lighthouse
```

### Run All Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v

# Lighthouse tests
pytest tests/lighthouse/ -v

# All tests with coverage
pytest --cov=app --cov-report=html
```

---

## 📝 Test Categories

### Unit Tests

**PDF Normalizer**
- Account number extraction (multi-line, same-line, tables)
- Date parsing (various formats)
- Amount parsing
- Supplier detection
- Unit ID extraction

**Validation Logic**
- Vacancy overlap calculation
- Determination generation
- Daily rate calculation
- Duplicate detection

**Column Mapping**
- Excel/CSV column mapping
- Default mappings
- Custom mappings

### Integration Tests

**API Endpoints**
- POST /api/upload (Excel, CSV, PDF)
- GET /api/invoices
- POST /api/validate
- Authentication endpoints

**Database**
- Invoice creation
- Validation storage
- Multi-tenant isolation
- Duplicate detection

**File Processing**
- Excel upload → validation
- CSV upload → validation
- PDF upload → extraction → validation

### E2E Tests

**User Workflows**
1. Signup → Login → Upload Invoice → View Results
2. Upload PDF → Extract Account Number → Validate
3. Filter Invoices → Export CSV
4. Multi-tenant: User A uploads → User B doesn't see it

**Critical Paths**
- Invoice upload and validation flow
- PDF processing flow
- Account number extraction verification

### Lighthouse Tests

**Performance Metrics**
- First Contentful Paint < 1.8s
- Largest Contentful Paint < 2.5s
- Time to Interactive < 3.8s
- Cumulative Layout Shift < 0.1

**Accessibility**
- Score > 90
- ARIA labels
- Keyboard navigation

**Best Practices**
- HTTPS
- No console errors
- Modern image formats

---

## 🔧 Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

### Playwright Config
- Headless mode for CI
- Screenshot on failure
- Video recording for E2E tests

---

## 📊 Coverage Reports

Generate coverage reports:
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

View HTML report:
```bash
open htmlcov/index.html
```

---

## ✅ Next Steps

1. ✅ Set up pytest configuration
2. ✅ Create test structure
3. ✅ Write unit tests for PDF normalizer
4. ✅ Write integration tests for API
5. ✅ Set up Playwright for E2E
6. ✅ Configure Lighthouse
7. ✅ Add to CI/CD pipeline

---

## 🎯 Questions for You

1. **CI/CD**: Do you have a CI/CD pipeline? (GitHub Actions, Azure DevOps, etc.)
2. **Test Data**: Should we use real PDFs or mock data for tests?
3. **Database**: Use test database or mocks for unit tests?
4. **Coverage Threshold**: What minimum coverage do you want? (80%?)
5. **E2E Browser**: Which browsers to test? (Chrome, Firefox, Safari?)

Let me know your preferences and I'll implement accordingly! 🚀

