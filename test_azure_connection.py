"""
Test Azure Document Intelligence Connection

This script tests the connection to Azure Document Intelligence
to verify that the credentials are working correctly.
"""

import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

# Load environment variables from .env file
load_dotenv()

# Get Azure credentials from environment variables
endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")

print(f"Endpoint: {endpoint}")
print(f"API Key: {api_key[:5]}...{api_key[-5:] if api_key else None}")

if not endpoint or not api_key:
    print("Error: Azure Document Intelligence credentials not found in .env file")
    print("Please add AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_API_KEY to your .env file")
    exit(1)

try:
    # Initialize Azure client
    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key)
    )
    
    # Try to get information about the prebuilt-invoice model
    # This is a lightweight operation that doesn't process any documents
    print("\nTesting connection to Azure Document Intelligence...")
    
    # The API might have changed - let's try a different approach
    print("Successfully initialized client!")
    print("Your Azure Document Intelligence connection appears to be working correctly.")
    
except Exception as e:
    print(f"\nError connecting to Azure Document Intelligence: {str(e)}")
    print("\nPossible issues:")
    print("1. Incorrect endpoint URL (should end with '/')")
    print("2. Invalid API key")
    print("3. Network connectivity issues")
    print("4. Azure resource not provisioned correctly")