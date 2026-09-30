# 🚀 How to Run All Tests

## 📋 **Quick Reference**

### **Run All Unit Tests**
```bash
python -m pytest tests/unit/ -v
```

### **Run All Integration Tests**
```bash
python -m pytest tests/integration/ -v -m integration
```

### **Run All Unit + Integration Tests**
```bash
python -m pytest tests/unit/ tests/integration/ -v
```

### **Run E2E Tests** (requires app running)
```bash
# Terminal 1: Start the application
uvicorn main:app --reload

# Terminal 2: Run E2E tests
python -m pytest tests/e2e/ -v -m e2e
```

### **Run Lighthouse Tests** (requires Lighthouse CLI)
```bash
# Install Lighthouse first
npm install -g lighthouse

# Run tests
python -m pytest tests/lighthouse/ -v -m lighthouse
```

### **Run Everything Except E2E and Lighthouse**
```bash
python -m pytest tests/ -v -m "not e2e and not lighthouse"
```

---

## 📊 **Test Coverage**

### **View Coverage Report**
```bash
# Generate HTML coverage report
python -m pytest tests/unit/ --cov=app --cov-report=html

# Open the report
# Windows: start htmlcov/index.html
# Mac/Linux: open htmlcov/index.html
```

### **Coverage by Category**
```bash
# Unit tests only
pytest tests/unit/ --cov=app --cov-report=term-missing

# Integration tests
pytest tests/integration/ --cov=app --cov-report=term-missing
```

---

## 🎯 **Test Categories**

### **Unit Tests** (44 tests)
- PDF Normalizer: 15 tests
- Validation Logic: 13 tests
- Column Mapping: 9 tests
- Date Parsing: 7 tests

**Run:** `pytest tests/unit/ -v`

### **Integration Tests** (8+ tests)
- API Endpoints: 8 tests
- File Upload: 3 tests
- Duplicate Detection: 1 test
- Multi-tenant: 1 test

**Run:** `pytest tests/integration/ -v -m integration`

### **E2E Tests** (13 tests)
- User Workflows: 6 tests
- Complete Workflows: 7 tests

**Run:** `pytest tests/e2e/ -v -m e2e` (requires app running)

### **Lighthouse Tests** (2 tests)
- Performance: 2 tests

**Run:** `pytest tests/lighthouse/ -v -m lighthouse` (requires Lighthouse CLI)

---

## ⚙️ **Configuration**

### **Test Database**
- **Unit Tests**: SQLite in-memory (fast, automatic)
- **Integration Tests**: SQLite by default, or Supabase if `TEST_DATABASE_URL` is set

### **Environment Variables**
```bash
# For Supabase integration tests
export TEST_DATABASE_URL=postgresql://user:pass@host:5432/test_db

# For E2E tests
export BASE_URL=http://localhost:8000
export PLAYWRIGHT_HEADLESS=true  # Set to false to see browser
```

---

## 🐛 **Troubleshooting**

### **Tests Fail with Database Errors**
- Check if test database is accessible
- For integration tests, verify `TEST_DATABASE_URL` if using Supabase
- Unit tests use SQLite in-memory (should work automatically)

### **E2E Tests Fail**
- Make sure app is running: `uvicorn main:app --reload`
- Check `BASE_URL` environment variable
- Verify test user exists in database

### **Lighthouse Tests Skip**
- Install Lighthouse CLI: `npm install -g lighthouse`
- Make sure app is running
- Tests will skip gracefully if Lighthouse not available

### **Import Errors**
- Make sure you're in the project root directory
- Check that all dependencies are installed: `pip install -r requirements.txt`

---

## 📈 **Test Results Summary**

**Expected Results:**
- ✅ Unit Tests: 44 passing
- ✅ Integration Tests: 8+ passing
- ✅ E2E Tests: 13 tests (may skip if app not running)
- ✅ Lighthouse Tests: 2 tests (may skip if Lighthouse not installed)

**Coverage:**
- Current: 32-47% (varies by test suite)
- Target: 80%+

---

## ✅ **Quick Verification**

```bash
# Quick test - run unit tests only
python -m pytest tests/unit/ -v --tb=short

# Should see: 44 passed
```

---

**Status**: ✅ **All test infrastructure ready!**

