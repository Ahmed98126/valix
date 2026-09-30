"""
Debug Server Error

This script attempts to diagnose the 500 Internal Server Error
by making requests to the server and examining the response.
"""

import requests
import sys

def debug_server_error():
    """Try to diagnose the 500 Internal Server Error."""
    url = "http://127.0.0.1:8000"
    
    print(f"Debugging server error at {url}...")
    
    try:
        # Make a request with verbose error information
        response = requests.get(url, headers={"Accept": "application/json"})
        
        print(f"Status code: {response.status_code}")
        print(f"Response size: {len(response.content)} bytes")
        
        # Try to get the error details
        try:
            print("\nResponse content:")
            print(response.content.decode('utf-8'))
        except UnicodeDecodeError:
            print("Response content is not UTF-8 encoded")
            print(response.content)
        
        # Check for specific error patterns
        content = response.content.lower()
        if b"database" in content:
            print("\nPossible database connection issue detected")
        if b"azure" in content:
            print("\nPossible Azure API issue detected")
        if b"import" in content or b"module" in content:
            print("\nPossible Python module import issue detected")
        if b"template" in content:
            print("\nPossible template rendering issue detected")
        
        return response
            
    except requests.exceptions.ConnectionError:
        print("Connection error: Could not connect to the server")
        print("Make sure the server is running on http://127.0.0.1:8000")
        return None
    except requests.exceptions.Timeout:
        print("Timeout error: The server took too long to respond")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    debug_server_error()