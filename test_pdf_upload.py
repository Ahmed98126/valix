"""Test PDF upload and processing workflow against a running local server.

Usage:
    Set TEST_EMAIL and TEST_PASSWORD environment variables, or you will be prompted:

        TEST_EMAIL=user@example.com TEST_PASSWORD=yourpassword python test_pdf_upload.py

    Requires the Valix server to be running at http://localhost:8000.
    The PDF file to upload must exist at the path specified below (defaults to
    "british gas energy bill.pdf" in the project root for local dev testing).
"""

import os
import getpass
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8000")


def test_pdf_upload() -> None:
    """Test the PDF upload workflow end-to-end."""
    email = os.environ.get("TEST_EMAIL") or input("Email: ").strip()
    password = os.environ.get("TEST_PASSWORD") or getpass.getpass("Password (input hidden): ")

    if not email or not password:
        print("Both email and password are required.")
        raise SystemExit(1)

    session = requests.Session()

    print(f"Logging in as: {email}")
    response = session.post(
        f"{BASE_URL}/login",
        data={"email": email, "password": password},
        allow_redirects=True,
    )

    if response.status_code not in (200, 302, 303):
        print(f"Login failed (status {response.status_code}).")
        print(response.text[:300])
        return

    print("Login accepted.")

    upload_page = session.get(f"{BASE_URL}/upload")
    if upload_page.status_code != 200:
        print(f"Upload page inaccessible (status {upload_page.status_code}).")
        return

    print("Upload page accessible.")

    # Use the path from environment, default to the local dev test file
    pdf_path = os.environ.get("TEST_PDF_PATH", "british gas energy bill.pdf")

    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        print("Set TEST_PDF_PATH to the path of a PDF file to upload.")
        return

    print(f"Uploading: {pdf_path}")
    with open(pdf_path, "rb") as pdf_file:
        files = {"file": (os.path.basename(pdf_path), pdf_file, "application/pdf")}
        response = session.post(f"{BASE_URL}/api/upload", files=files)

    if response.status_code in (200, 302, 303):
        print("Upload request accepted.")
        print(response.text[:500])
    else:
        print(f"Upload failed (status {response.status_code}).")
        print(response.text[:300])


if __name__ == "__main__":
    test_pdf_upload()
