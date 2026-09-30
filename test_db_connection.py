"""
Test Database Connection

This script tests the connection to the database to verify
that the credentials are working correctly.
"""

import os
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import text

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
database_url = os.getenv("DATABASE_URL")

print(f"Database URL: {database_url[:20]}...{database_url[-20:] if database_url else None}")

if not database_url:
    print("Error: DATABASE_URL not found in .env file")
    print("Please add DATABASE_URL to your .env file")
    exit(1)

try:
    # Create engine
    engine = sqlalchemy.create_engine(database_url)
    
    # Test connection
    print("\nTesting connection to database...")
    
    with engine.connect() as connection:
        # Execute a simple query
        result = connection.execute(text("SELECT 1"))
        row = result.fetchone()
        
        if row and row[0] == 1:
            print("Successfully connected to the database!")
            
            # Check if tables exist
            print("\nChecking for required tables...")
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            
            print(f"Found {len(tables)} tables:")
            for table in tables[:10]:  # Show first 10 tables
                print(f"- {table}")
                
            if len(tables) > 10:
                print(f"... and {len(tables) - 10} more")
                
            # Check for specific tables
            required_tables = ["tenants", "users", "invoices", "units", "leases", "invoice_validation"]
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"\nWarning: Missing required tables: {', '.join(missing_tables)}")
                print("You may need to initialize the database with: python -m app.db")
            else:
                print("\nAll required tables exist!")
        else:
            print("Error: Unexpected result from database query")
    
except Exception as e:
    print(f"\nError connecting to database: {str(e)}")
    print("\nPossible issues:")
    print("1. Incorrect database URL")
    print("2. Database server is not running")
    print("3. Network connectivity issues")
    print("4. Firewall blocking connection")
    print("5. Invalid credentials")