"""Test the forgot-password flow against a running local server.

Usage:
    Set TEST_EMAIL environment variable, or you will be prompted:

        TEST_EMAIL=user@example.com python test_forgot_password.py

    Requires the Valix server to be running at http://localhost:8000.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


def test_forgot_password(base_url: str = "http://localhost:8000") -> None:
    """POST to /forgot-password and report the result."""
    email = os.environ.get("TEST_EMAIL") or input("Email to test with: ").strip()
    if not email:
        print("Email is required.")
        raise SystemExit(1)

    forgot_password_url = f"{base_url}/forgot-password"
    print(f"Testing forgot-password for: {email}")

    response = requests.post(forgot_password_url, data={"email": email})

    if response.status_code in (200, 302, 303):
        print(f"Request accepted (status {response.status_code}).")
        print(f"Final URL: {response.url}")
        if "success" in response.url:
            print("Success message present in redirect URL.")
            print("Check the inbox for the password reset link.")
        else:
            print("No success indicator in redirect URL — check server logs.")
    else:
        print(f"Unexpected status code: {response.status_code}")
        print(response.text[:300])


if __name__ == "__main__":
    test_forgot_password()
