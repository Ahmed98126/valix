"""Test different Supabase pooler regions.

Usage:
    Set the following environment variables before running, or export them in your shell:

        SUPABASE_DB_PASSWORD=<your-db-password>
        SUPABASE_PROJECT_REF=<your-project-ref>

    Then run:
        python scripts/test_pooler_regions.py

    The working connection string (if found) will be printed so you can copy it
    into DATABASE_URL in your .env file.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

# ── Credentials from environment (never hard-code these) ──────────────────────
password = os.environ.get("SUPABASE_DB_PASSWORD")
project_ref = os.environ.get("SUPABASE_PROJECT_REF")

if not password or not project_ref:
    print("ERROR: SUPABASE_DB_PASSWORD and SUPABASE_PROJECT_REF must be set as environment variables.")
    print("  export SUPABASE_DB_PASSWORD=<your-db-password>")
    print("  export SUPABASE_PROJECT_REF=<your-project-ref>")
    sys.exit(1)
# ──────────────────────────────────────────────────────────────────────────────

# Common Supabase pooler regions
regions = [
    "us-east-1",
    "us-west-1",
    "eu-west-1",
    "eu-west-2",
    "ap-southeast-1",
    "ap-southeast-2",
]

print("Testing Session Pooler with different regions...\n")

for region in regions:
    connection_string = (
        f"postgresql://postgres.{project_ref}:{password}"
        f"@aws-0-{region}.pooler.supabase.com:5432/postgres"
    )

    try:
        print(f"Testing {region}...", end=" ")
        engine = create_engine(connection_string, pool_pre_ping=True)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print("SUCCESS!")
            print(f"\nWorking region: {region}")
            print("Copy this into your .env as DATABASE_URL:")
            # Print the working string with the password redacted so the console
            # log stays clean.  The user knows their own password.
            safe = connection_string.replace(f":{password}@", ":***@")
            print(safe)
            sys.exit(0)

    except Exception as e:
        error_msg = str(e)
        if "Tenant or user not found" in error_msg:
            print("Wrong region")
        elif "could not translate host name" in error_msg:
            print("DNS error")
        else:
            print(f"Error: {error_msg[:60]}")

print("\nNone of the common regions worked.")
print("Get the exact connection string from: Settings -> Database -> Connection string -> Session Pooler")
