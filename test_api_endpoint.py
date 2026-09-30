"""
Test API Endpoint

This script tests if the API endpoints are accessible.
"""

import requests

def test_api():
    """Test if the API endpoints are accessible."""
    base_url = "http://127.0.0.1:8000"
    
    # Test the API documentation endpoint
    docs_url = f"{base_url}/docs"
    print(f"Testing API docs at {docs_url}...")
    
    try:
        response = requests.get(docs_url)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("API docs are accessible!")
            return True
        else:
            print(f"API docs returned an unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Connection error: Could not connect to the server")
        return False
    except requests.exceptions.Timeout:
        print("Timeout error: The server took too long to respond")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_api()