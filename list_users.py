import os
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import text

load_dotenv()
database_url = os.getenv('DATABASE_URL')
engine = sqlalchemy.create_engine(database_url)

with engine.connect() as connection:
    result = connection.execute(text('SELECT email, full_name, is_active FROM users ORDER BY created_at;'))
    users = result.fetchall()
    print('Available users:')
    for user in users:
        status = 'Active' if user[2] else 'Inactive'
        name = user[1] if user[1] else 'No name'
        print(f'  - {user[0]} ({name}) - {status}')