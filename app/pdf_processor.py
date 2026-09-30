"""PDF Invoice Processor using Azure Document Intelligence.

This module handles the interaction with Azure Document Intelligence API
to extract structured data from PDF invoices.
"""

import os
import logging
from typing import Dict, Optional, Any
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from app.normalize_account_numbers import normalize_account_number

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF invoice extraction using Azure Document Intelligence."""
    
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the PDF processor.
        
        Args:
            endpoint: Azure Document Intelligence endpoint URL
            api_key: Azure Document Intelligence API key
        
        If not provided, will read from environment variables:
            AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
            AZURE_DOCUMENT_INTELLIGENCE_API_KEY
        """
        self.endpoint = endpoint or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
        
        if not self.endpoint or not self.api_key:
            raise ValueError(
                "Azure Document Intelligence credentials not found. "
                "Please set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and "
                "AZURE_DOCUMENT_INTELLIGENCE_API_KEY environment variables."
            )
        
        # Initialize Azure client
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
        
        logger.info("PDF Processor initialized with Azure Document Intelligence")
    
    def extract_invoice(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract structured data from a PDF invoice.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Dictionary containing extracted invoice data in Azure Document Intelligence format
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If extraction fails
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting invoice data from: {pdf_path.name}")
        
        try:
            # Read PDF file
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            
            # Use prebuilt Invoice model
            # Azure Document Intelligence has a prebuilt invoice model
            # that extracts common invoice fields automatically
            # Note: SDK v1.0+ requires 'body' parameter with bytes or AnalyzeDocumentRequest
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-invoice",  # Prebuilt invoice model
                body=pdf_data,  # Pass PDF bytes directly as body
                content_type="application/pdf"
            )
            
            # Wait for analysis to complete
            result = poller.result()
            
            logger.info(f"Successfully extracted data from {pdf_path.name}")
            
            # Convert result to dictionary
            extracted_data = self._convert_to_dict(result)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting invoice from {pdf_path.name}: {str(e)}")
            raise Exception(f"Failed to extract invoice data: {str(e)}")
    
    def _convert_to_dict(self, result: Any) -> Dict[str, Any]:
        """
        Convert Azure Document Intelligence result to dictionary.
        
        Args:
            result: Azure Document Intelligence analysis result
        
        Returns:
            Dictionary representation of the result
        """
        extracted = {
            "model_id": result.model_id,
            "content": result.content if hasattr(result, 'content') else None,
            "pages": [],
            "fields": {},
            "tables": [],
            "confidence": None
        }
        
        # Extract pages
        if hasattr(result, 'pages') and result.pages:
            for page in result.pages:
                page_data = {
                    "page_number": page.page_number if hasattr(page, 'page_number') else None,
                    "width": page.width if hasattr(page, 'width') else None,
                    "height": page.height if hasattr(page, 'height') else None,
                    "unit": page.unit if hasattr(page, 'unit') else None
                }
                extracted["pages"].append(page_data)
        
        # Extract fields (invoice-specific fields)
        if hasattr(result, 'documents') and result.documents:
            for doc in result.documents:
                if hasattr(doc, 'fields'):
                    for field_name, field_value in doc.fields.items():
                        extracted["fields"][field_name] = self._extract_field_value(field_value)
        
        # Extract tables
        if hasattr(result, 'tables') and result.tables:
            for table in result.tables:
                table_data = {
                    "row_count": table.row_count if hasattr(table, 'row_count') else 0,
                    "column_count": table.column_count if hasattr(table, 'column_count') else 0,
                    "cells": []
                }
                
                if hasattr(table, 'cells'):
                    for cell in table.cells:
                        cell_data = {
                            "row_index": cell.row_index if hasattr(cell, 'row_index') else None,
                            "column_index": cell.column_index if hasattr(cell, 'column_index') else None,
                            "content": cell.content if hasattr(cell, 'content') else None,
                            "kind": cell.kind if hasattr(cell, 'kind') else None
                        }
                        table_data["cells"].append(cell_data)
                
                extracted["tables"].append(table_data)
        
        # Extract overall confidence if available
        if hasattr(result, 'confidence'):
            extracted["confidence"] = result.confidence
        
        return extracted
    
    def _extract_field_value(self, field_value: Any) -> Dict[str, Any]:
        """
        Extract value from an Azure Document Intelligence field.
        
        Args:
            field_value: Field value object from Azure
        
        Returns:
            Dictionary with value, confidence, and content
        """
        extracted = {
            "value": None,
            "content": None,
            "confidence": None
        }
        
        if hasattr(field_value, 'content'):
            extracted["content"] = field_value.content
        
        if hasattr(field_value, 'confidence'):
            extracted["confidence"] = field_value.confidence
        
        # Extract actual value based on field type
        if hasattr(field_value, 'value_string'):
            extracted["value"] = field_value.value_string
        elif hasattr(field_value, 'value_number'):
            extracted["value"] = field_value.value_number
        elif hasattr(field_value, 'value_date'):
            extracted["value"] = field_value.value_date
        elif hasattr(field_value, 'value_time'):
            extracted["value"] = field_value.value_time
        elif hasattr(field_value, 'value_phone_number'):
            extracted["value"] = field_value.value_phone_number
        elif hasattr(field_value, 'value_address'):
            # Address is a complex type
            if field_value.value_address:
                addr = field_value.value_address
                extracted["value"] = {
                    "street_address": getattr(addr, 'street_address', None),
                    "city": getattr(addr, 'city', None),
                    "state": getattr(addr, 'state', None),
                    "postal_code": getattr(addr, 'postal_code', None),
                    "country_region": getattr(addr, 'country_region', None)
                }
        elif hasattr(field_value, 'value_array'):
            # Array of values
            extracted["value"] = [
                self._extract_field_value(item) for item in field_value.value_array
            ]
        elif hasattr(field_value, 'value_object'):
            # Object with nested fields
            extracted["value"] = {
                key: self._extract_field_value(val)
                for key, val in field_value.value_object.items()
            }
        else:
            # Fallback to content
            extracted["value"] = extracted.get("content")
        
        return extracted


def extract_pdf_invoice(pdf_path: str) -> Dict[str, Any]:
    """
    Convenience function to extract invoice data from PDF.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Dictionary containing extracted invoice data
    """
    processor = PDFProcessor()
    return processor.extract_invoice(pdf_path)



