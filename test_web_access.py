"""Test web interface access."""

import requests

def test_web_access():
    """Test access to web interface."""
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Try to access the dashboard (should redirect to login if not authenticated)
    dashboard_url = "http://localhost:8000/dashboard"
    print(f"Accessing {dashboard_url}...")
    response = session.get(dashboard_url)
    
    print(f"Status code: {response.status_code}")
    print(f"URL after redirect: {response.url}")
    
    if response.status_code == 200:
        print("Access successful!")
        print(response.text[:500])  # Print first 500 chars of response
    else:
        print("Access failed or redirected.")
        print(response.text[:500])
    
    # Try to access the login page
    login_url = "http://localhost:8000/login"
    print(f"\nAccessing {login_url}...")
    response = session.get(login_url)
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("Access to login page successful!")
        print(response.text[:500])  # Print first 500 chars of response
    else:
        print("Access to login page failed.")
        print(response.text[:500])

if __name__ == "__main__":
    test_web_access()