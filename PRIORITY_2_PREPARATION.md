# Priority 2: Production Setup - Preparation Guide

## Overview

This guide prepares for production deployment, including PostgreSQL migration, environment configuration, and deployment setup.

---

## 1. PostgreSQL Migration

### Current State
- Using SQLite for development (`app.db`)
- All models support PostgreSQL (via SQLAlchemy)
- Multi-tenant architecture ready for production

### Migration Steps

#### Step 1: Set Up PostgreSQL Database
```bash
# Install PostgreSQL (if not already installed)
# Create database and user
createdb invoice_validator
createuser invoice_validator_user
psql invoice_validator -c "ALTER USER invoice_validator_user WITH PASSWORD 'your_secure_password';"
psql invoice_validator -c "GRANT ALL PRIVILEGES ON DATABASE invoice_validator TO invoice_validator_user;"
```

#### Step 2: Create Migration Script
**File: `scripts/migrate_to_postgresql.py`**

```python
"""
Migrate data from SQLite to PostgreSQL.

This script:
1. Connects to SQLite source database
2. Connects to PostgreSQL target database
3. Migrates all data preserving relationships
4. Verifies data integrity
"""
```

**Key Features:**
- Preserve all tenant data
- Maintain referential integrity
- Handle foreign key relationships
- Verify data counts match
- Rollback capability

#### Step 3: Update Configuration
**File: `app/config.py`**

```python
# Production database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://invoice_validator_user:password@localhost/invoice_validator"
)
```

#### Step 4: Test Migration
- Test with development data
- Verify all tables migrated
- Test queries and relationships
- Performance testing

---

## 2. Environment Configuration

### Environment Variables

Create `.env` file for production:
```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Security
SECRET_KEY=your-secret-key-min-32-chars-change-in-production
SESSION_SECRET=your-session-secret-min-32-chars

# Application
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
UPLOAD_DIR=/var/uploads

# Email (for future notifications)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
```

### Configuration Management

**File: `app/config.py`** (update)
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    max_upload_size: int = 10485760
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
```

---

## 3. Deployment Guide

### Option A: Cloud Platform (Recommended)

#### AWS (EC2 + RDS)
1. **EC2 Instance Setup**:
   - Ubuntu 22.04 LTS
   - Install Python 3.11+
   - Install PostgreSQL client
   - Set up firewall rules

2. **RDS PostgreSQL Setup**:
   - Create RDS PostgreSQL instance
   - Configure security groups
   - Set up automated backups

3. **Application Deployment**:
   - Use systemd service
   - Set up reverse proxy (Nginx)
   - SSL certificate (Let's Encrypt)
   - Environment variables

#### Azure (App Service + Azure Database)
1. **App Service Setup**:
   - Create Python web app
   - Configure deployment
   - Set environment variables

2. **Azure Database for PostgreSQL**:
   - Create database instance
   - Configure firewall rules
   - Set up connection string

#### Google Cloud (Cloud Run + Cloud SQL)
1. **Cloud Run Setup**:
   - Containerize application
   - Deploy to Cloud Run
   - Configure environment variables

2. **Cloud SQL Setup**:
   - Create PostgreSQL instance
   - Configure connections
   - Set up backups

### Option B: Docker Deployment

**File: `Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/invoice_validator
    depends_on:
      - db
    
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=invoice_validator
      - POSTGRES_USER=invoice_validator_user
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 4. Security Checklist

- [ ] Change default secret keys
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Configure database access restrictions
- [ ] Enable database backups
- [ ] Set up log rotation
- [ ] Configure rate limiting
- [ ] Enable CORS properly
- [ ] Sanitize file uploads
- [ ] Set up monitoring and alerts

---

## 5. Monitoring & Logging

### Application Logging
- Use Python `logging` module
- Log to files and/or cloud logging service
- Set appropriate log levels
- Include request IDs for tracing

### Monitoring
- Application health checks
- Database connection monitoring
- File upload monitoring
- Error rate tracking
- Performance metrics

---

## 6. Backup Strategy

### Database Backups
- Daily automated backups
- Weekly full backups
- Monthly archive backups
- Test restore procedures

### File Backups
- Uploaded files backup
- Configuration backup
- Regular backup verification

---

## 7. Testing Checklist

Before going live:
- [ ] Test PostgreSQL migration
- [ ] Test all endpoints with production database
- [ ] Test file uploads
- [ ] Test multi-tenant isolation
- [ ] Test error handling
- [ ] Test pagination with large datasets
- [ ] Performance testing
- [ ] Security testing
- [ ] Backup/restore testing
- [ ] Load testing

---

## 8. Deployment Steps

### Pre-Deployment
1. Review and update configuration
2. Run database migration
3. Test in staging environment
4. Review security checklist
5. Set up monitoring

### Deployment
1. Deploy application
2. Run database migrations
3. Verify application starts
4. Test critical paths
5. Monitor logs

### Post-Deployment
1. Verify all features work
2. Monitor error rates
3. Check performance metrics
4. Review user feedback
5. Schedule regular maintenance

---

## Next Steps

1. **This Week**: Prepare migration script
2. **Next Week**: Set up PostgreSQL database
3. **Next Week**: Test migration with sample data
4. **Next Week**: Choose deployment platform
5. **Next Week**: Create deployment documentation

---

## Resources

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- SQLAlchemy PostgreSQL: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html


