"""Test login functionality against a running local server.

Usage:
    Set TEST_EMAIL and TEST_PASSWORD environment variables, or you will be prompted:

        TEST_EMAIL=user@example.com TEST_PASSWORD=yourpassword python test_login.py

    Requires the Valix server to be running at http://localhost:8000.
"""

import os
import getpass
import requests


def test_login(email: str, password: str, base_url: str = "http://localhost:8000") -> None:
    """Send a login request and report the result."""
    login_url = f"{base_url}/login"
    print(f"Testing login for: {email}")

    session = requests.Session()
    response = session.post(
        login_url,
        data={"email": email, "password": password},
        allow_redirects=True,
    )

    print(f"Status code: {response.status_code}")
    print(f"Final URL:   {response.url}")

    if "dashboard" in response.url:
        print("Login successful — redirected to dashboard.")
        dashboard = session.get(f"{base_url}/dashboard")
        print(f"Dashboard status: {dashboard.status_code}")
        if dashboard.status_code == 200:
            print("Dashboard accessible.")
        else:
            print(f"Dashboard returned unexpected status: {dashboard.status_code}")
    else:
        print("Login did not reach dashboard.")
        print("Response snippet:", response.text[:300])


if __name__ == "__main__":
    email = os.environ.get("TEST_EMAIL") or input("Email: ").strip()
    password = os.environ.get("TEST_PASSWORD") or getpass.getpass("Password (input hidden): ")

    if not email or not password:
        print("Both email and password are required.")
        raise SystemExit(1)

    test_login(email, password)
