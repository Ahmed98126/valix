import os
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import text

load_dotenv()
database_url = os.getenv('DATABASE_URL')
print(f'Testing Supabase connection...')

try:
    engine = sqlalchemy.create_engine(database_url)
    with engine.connect() as connection:
        result = connection.execute(text('SELECT version();'))
        version = result.fetchone()[0]
        print('SUCCESS: Database connection working!')
        print(f'PostgreSQL version: {version[:50]}...')
        
        # Check users table
        result = connection.execute(text("SELECT COUNT(*) FROM users;"))
        user_count = result.fetchone()[0]
        print(f'Users in database: {user_count}')
        
except Exception as e:
    print(f'FAILED: {str(e)}')