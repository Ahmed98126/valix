import os
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import text

load_dotenv()
database_url = os.getenv('DATABASE_URL')
print(f'Testing connection to: {database_url[:50]}...')

try:
    engine = sqlalchemy.create_engine(database_url)
    with engine.connect() as connection:
        result = connection.execute(text('SELECT version();'))
        version = result.fetchone()[0]
        print('✅ Database connection successful!')
        print(f'PostgreSQL version: {version}')
        
        # Check if main tables exist
        result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
        tables = [row[0] for row in result.fetchall()]
        print(f'Tables found: {tables}')
        
except Exception as e:
    print(f'❌ Database connection failed: {str(e)}')