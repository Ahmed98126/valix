"""
Test Specific API Endpoints

This script tests specific API endpoints to identify where the error is occurring.
"""

import requests

def test_endpoints():
    """Test various API endpoints."""
    base_url = "http://127.0.0.1:8000"
    
    endpoints = [
        "/docs",           # API documentation
        "/openapi.json",   # OpenAPI schema
        "/api/health",     # Health check (if available)
        "/login",          # Login page
        "/dashboard",      # Dashboard page
        "/upload",         # Upload page
    ]
    
    results = {}
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\nTesting endpoint: {url}")
        
        try:
            response = requests.get(url)
            status = response.status_code
            results[endpoint] = status
            
            print(f"Status code: {status}")
            
            if status == 200:
                print("Endpoint is accessible!")
                content_type = response.headers.get("content-type", "")
                print(f"Content type: {content_type}")
                
                if "text/html" in content_type:
                    print("Response is HTML")
                elif "application/json" in content_type:
                    print("Response is JSON")
                    print(f"Response: {response.json()}")
            else:
                print(f"Endpoint returned an unexpected status code: {status}")
                
        except requests.exceptions.ConnectionError:
            print("Connection error: Could not connect to the server")
            results[endpoint] = "Connection Error"
        except requests.exceptions.Timeout:
            print("Timeout error: The server took too long to respond")
            results[endpoint] = "Timeout"
        except Exception as e:
            print(f"Error: {str(e)}")
            results[endpoint] = f"Error: {str(e)}"
    
    print("\n--- Summary ---")
    for endpoint, status in results.items():
        print(f"{endpoint}: {status}")
    
    return results

if __name__ == "__main__":
    test_endpoints()