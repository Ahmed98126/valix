"""
Test Web Server Accessibility

This script tests if the web server is accessible and returns the expected response.
"""

import requests
import time

def test_server():
    """Test if the server is accessible."""
    url = "http://127.0.0.1:8000"
    
    print(f"Testing connection to {url}...")
    
    try:
        response = requests.get(url, timeout=5)
        
        print(f"Status code: {response.status_code}")
        print(f"Response size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("Server is accessible!")
            print("\nResponse headers:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
            
            # Check if it's an HTML response (likely the login page)
            if "text/html" in response.headers.get("content-type", ""):
                print("\nResponse appears to be an HTML page (likely the login page)")
                
                # Check for common elements in the login page
                if b"login" in response.content.lower() or b"sign in" in response.content.lower():
                    print("Page contains login-related content")
                else:
                    print("Page does not appear to be a login page")
            
            return True
        else:
            print(f"Server returned an unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Connection error: Could not connect to the server")
        print("Make sure the server is running on http://127.0.0.1:8000")
        return False
    except requests.exceptions.Timeout:
        print("Timeout error: The server took too long to respond")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Try up to 3 times with a 2-second delay between attempts
    for attempt in range(1, 4):
        print(f"Attempt {attempt}/3:")
        if test_server():
            break
        elif attempt < 3:
            print(f"Retrying in 2 seconds...\n")
            time.sleep(2)
        else:
            print("All attempts failed. Please check if the server is running correctly.")