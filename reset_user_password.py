"""Reset a user's password directly in the database — interactive admin utility.

Usage:
    python reset_user_password.py

You will be prompted for the target email address and the new password.
Never hard-code credentials in this file.
"""

import getpass
from app.db import SessionLocal
from app.models import User


def reset_password(email: str, new_password: str) -> bool:
    """Reset a user's password. Returns True on success, False if user not found."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()

        if not user:
            print(f"User with email '{email}' not found.")
            return False

        user.set_password(new_password)
        session.commit()
        print(f"Password for '{email}' has been reset successfully.")
        return True
    finally:
        session.close()


if __name__ == "__main__":
    print("=== Valix — Admin Password Reset ===")
    email = input("Target user email: ").strip()
    if not email:
        print("Email is required.")
        raise SystemExit(1)

    new_password = getpass.getpass("New password (input hidden): ")
    confirm = getpass.getpass("Confirm new password: ")

    if new_password != confirm:
        print("Passwords do not match. Aborting.")
        raise SystemExit(1)

    if len(new_password) < 8:
        print("Password must be at least 8 characters. Aborting.")
        raise SystemExit(1)

    reset_password(email, new_password)
