# 🗄️ Test Database Strategy

## Overview

We use **Supabase (PostgreSQL)** for production, but have a flexible test database strategy:

---

## 📊 Database Strategy by Test Type

### **Unit Tests** → SQLite In-Memory
- **Why**: Fast, no external dependencies, isolated
- **Speed**: < 1 second per test
- **Setup**: Automatic, no configuration needed
- **Use Case**: Testing individual functions (PDF normalizer, validation logic)

### **Integration Tests** → Supabase Test Database (or SQLite)
- **Why**: Test real database interactions, PostgreSQL features
- **Speed**: 1-5 seconds per test
- **Setup**: Requires TEST_DATABASE_URL environment variable
- **Use Case**: Testing API endpoints, database operations

---

## 🔧 Configuration

### Option 1: Use Supabase Test Database (Recommended for Integration Tests)

Create a **separate test database** in Supabase:

1. **Create Test Project in Supabase**:
   - Go to Supabase Dashboard
   - Create a new project (e.g., "invoice-validator-test")
   - Get the connection string

2. **Set Environment Variable**:
   ```bash
   # Windows PowerShell
   $env:TEST_DATABASE_URL="postgresql://postgres:password@host:5432/postgres"
   
   # Linux/Mac
   export TEST_DATABASE_URL="postgresql://postgres:password@host:5432/postgres"
   ```

3. **Run Integration Tests**:
   ```bash
   pytest -m integration
   ```

### Option 2: Use SQLite for All Tests (Default)

If `TEST_DATABASE_URL` is not set, tests use SQLite in-memory:

```bash
# No setup needed - works out of the box
pytest
```

**Benefits**:
- ✅ Fast execution
- ✅ No external dependencies
- ✅ Works offline
- ✅ Perfect for unit tests

**Limitations**:
- ⚠️ Some PostgreSQL-specific features won't be tested
- ⚠️ Different behavior than production database

---

## 🎯 Recommended Setup

### For Development:
```bash
# Unit tests: SQLite (fast)
pytest -m unit

# Integration tests: SQLite (fast, good enough for most cases)
pytest -m integration
```

### For CI/CD (Future):
```bash
# Set TEST_DATABASE_URL to Supabase test database
export TEST_DATABASE_URL="postgresql://..."
pytest -m integration
```

### For Production-Like Testing:
```bash
# Use Supabase test database
export TEST_DATABASE_URL="postgresql://..."
pytest -m integration
```

---

## 📝 Current Implementation

**Test Configuration** (`tests/conftest.py`):

```python
# Default: SQLite in-memory (fast, no setup)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "sqlite:///:memory:"  # Fast unit tests
)

# If TEST_DATABASE_URL is set, uses Supabase/PostgreSQL
# Example: TEST_DATABASE_URL=postgresql://user:pass@host:5432/test_db
```

---

## ✅ Best Practices

1. **Unit Tests**: Always use SQLite (fast, isolated)
2. **Integration Tests**: 
   - Use SQLite for development (fast)
   - Use Supabase test database for CI/CD (production-like)
3. **E2E Tests**: Use test Supabase database or staging environment
4. **Never**: Use production database for tests!

---

## 🔒 Security Note

**Never commit test database credentials!**

Use environment variables:
- `.env.test` (gitignored)
- CI/CD secrets
- Local environment variables

---

## 🚀 Quick Start

### Default (SQLite - Works Immediately):
```bash
pytest  # Uses SQLite in-memory
```

### With Supabase Test Database:
```bash
# Set environment variable
$env:TEST_DATABASE_URL="postgresql://..."

# Run tests
pytest -m integration
```

---

## 📊 Summary

| Test Type | Database | Speed | Setup | Use When |
|-----------|----------|-------|-------|----------|
| Unit | SQLite in-memory | Fast | None | Always |
| Integration | SQLite (default) | Fast | None | Development |
| Integration | Supabase (optional) | Medium | Env var | CI/CD, Production-like testing |
| E2E | Supabase test DB | Slow | Full setup | Pre-production testing |

---

**Bottom Line**: 
- ✅ **Unit tests** = SQLite (automatic, fast)
- ✅ **Integration tests** = SQLite by default, Supabase if `TEST_DATABASE_URL` is set
- ✅ **Production** = Supabase (always)

This gives you the best of both worlds: fast tests by default, with the option to test against real PostgreSQL when needed! 🚀

