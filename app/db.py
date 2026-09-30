"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Generator

from app.config import DATABASE_URL
from app.models import Base
from app.upload_status import UploadStatus  # Import to register table
from app.password_reset import PasswordResetToken  # Import to register table
from app.email_verification import EmailVerificationToken  # Import to register table


# Create SQLAlchemy engine
# Handle both SQLite and PostgreSQL
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}  # SQLite only
else:
    # PostgreSQL (Supabase) - use connection pooling
    connect_args = {
        "connect_timeout": 10,
    }

engine: Engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set to True for SQL query logging during development
    pool_pre_ping=True,  # Verify connections before using (PostgreSQL)
    pool_size=3,  # Base pool size (increased from 2 for better concurrency)
    max_overflow=7,  # Max overflow connections (total: 10 connections max)
    pool_recycle=1800,  # Recycle connections after 30 minutes (reduced from 1 hour)
    pool_timeout=30,  # Wait up to 30 seconds for a connection from the pool
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
    """
    Get a database session with proper cleanup.
    This is a dependency for FastAPI endpoints.
    Sessions are automatically closed after the request completes.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """
    Initialize the database by creating all tables.
    Call this once to set up the database schema.
    """
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized. Tables created in: {DATABASE_URL}")


if __name__ == "__main__":
    # Allow running this script directly to initialize the database
    init_db()

