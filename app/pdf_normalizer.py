"""PDF Invoice Normalizer.

This module converts the structured JSON output from Azure Document Intelligence
into the application's standard Invoice schema format, making it compatible
with the existing validation engine.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import re
from app.account_mapping import normalize_account_number

logger = logging.getLogger(__name__)


class PDFNormalizer:
    """Normalizes PDF extraction results to Invoice schema."""
    
    # Common UK energy supplier names (for matching)
    UK_ENERGY_SUPPLIERS = [
        "british gas", "eon", "e.on", "e.on energy", "octopus", "octopus energy",
        "edf", "npower", "scottish power", "sse", "utility warehouse",
        "ovo", "bulb", "shell energy", "green energy", "ecotricity"
    ]
    
    # Common utility types
    UTILITY_TYPES = ["electricity", "gas", "water", "energy"]
    
    def __init__(self, supplier_name: Optional[str] = None):
        """
        Initialize the normalizer.
        
        Args:
            supplier_name: Optional supplier name for supplier-specific normalization
        """
        self.supplier_name = supplier_name.lower() if supplier_name else None
        logger.info(f"PDF Normalizer initialized (supplier: {supplier_name or 'generic'})")
    
    def _clean_text(self, text: Optional[str], remove_all_spaces: bool = False) -> Optional[str]:
        """
        Clean extracted text by removing newlines and normalizing whitespace.
        
        Args:
            text: Text to clean
            remove_all_spaces: If True, remove all spaces (useful for account numbers)
            
        Returns:
            Cleaned text or None
        """
        if not text:
            return None
        
        # Convert to string if not already
        text_str = str(text)
        
        # Replace newlines with spaces
        text_str = text_str.replace('\n', ' ').replace('\r', ' ')
        
        if remove_all_spaces:
            # For account numbers, remove all spaces
            text_str = re.sub(r'\s+', '', text_str)
        else:
            # Normalize whitespace (multiple spaces to single space)
            text_str = re.sub(r'\s+', ' ', text_str)
        
        # Strip leading/trailing whitespace
        text_str = text_str.strip()
        
        return text_str if text_str else None
    
    def normalize(self, extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize extracted PDF data to Invoice schema format.
        
        Args:
            extracted_data: Dictionary from Azure Document Intelligence
        
        Returns:
            List of normalized invoice dictionaries (one invoice per PDF, or multiple if split)
        """
        try:
            # Extract fields from Azure response
            fields = extracted_data.get("fields", {})
            
            # Create normalized invoice
            invoice = self._create_invoice_dict(fields, extracted_data)
            
            # Validate required fields before returning
            if invoice and invoice.get("invoice_number"):
                # Check if supplier_account_number is missing or invalid
                account_number = invoice.get("supplier_account_number")
                invoice_number = invoice.get("invoice_number")
                
                if not account_number or account_number == "UNKNOWN" or account_number == invoice_number:
                    logger.warning(f"Missing or invalid supplier_account_number for invoice {invoice_number}. Account number: {account_number}. Account number is required and must be different from invoice number.")
                    # Don't return invalid invoice - let validation catch it
                    return []
                logger.info(f"Successfully normalized invoice {invoice_number} with account number {account_number}")
                return [invoice]
            else:
                logger.warning(f"Could not extract valid invoice from PDF. Invoice number: {invoice.get('invoice_number') if invoice else 'None'}")
                return []
                
        except Exception as e:
            logger.error(f"Error normalizing PDF data: {str(e)}")
            raise Exception(f"Failed to normalize invoice data: {str(e)}")
    
    def _create_invoice_dict(self, fields: Dict[str, Any], full_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a normalized invoice dictionary from extracted fields.
        
        Args:
            fields: Extracted fields from Azure
            full_data: Full extraction data (for tables, etc.)
        
        Returns:
            Normalized invoice dictionary
        """
        invoice = {
            "invoice_number": None,
            "supplier_name": None,
            "supplier_account_number": None,
            "unit_id": None,
            "address": None,  # Full address from invoice
            "billing_period_start": None,
            "billing_period_end": None,
            "invoice_date": None,
            "gross_amount": None,
            "net_amount": None,
            "vat_amount": None,
            "utility_type": "Electricity",  # Default
            "currency": "GBP",  # Default for UK
            "raw_data": full_data  # Store full extraction for debugging
        }
        
        # Map Azure invoice fields to our schema
        # Azure Document Intelligence prebuilt-invoice model provides these fields:
        
        # Invoice ID / Number
        invoice["invoice_number"] = self._extract_field(fields, [
            "InvoiceId", "InvoiceNumber", "Invoice ID", "DocumentNumber"
        ])
        
        # If no invoice number in fields, try to extract from content (for British Gas, etc.)
        if not invoice["invoice_number"]:
            content = full_data.get("content", "")
            if content:
                # Look for patterns like "Bill date: 04 March 2010" and use date as fallback
                # Or look for invoice/bill number patterns
                invoice_patterns = [
                    r'invoice\s+number[\s:]+([A-Z0-9-]+)',
                    r'bill\s+number[\s:]+([A-Z0-9-]+)',
                    r'invoice\s+no[\s:\.]+([A-Z0-9-]+)',
                ]
                for pattern in invoice_patterns:
                    inv_match = re.search(pattern, content, re.IGNORECASE)
                    if inv_match:
                        invoice["invoice_number"] = inv_match.group(1).strip()
                        logger.info(f"Found invoice number in content: {invoice['invoice_number']}")
                        break
        
        # Supplier / Vendor
        supplier = self._extract_field(fields, [
            "VendorName", "SupplierName", "Vendor", "Supplier", "CompanyName"
        ])
        supplier_cleaned = self._clean_text(supplier) if supplier else None
        invoice["supplier_name"] = supplier_cleaned or "Unknown Supplier"
        
        # Invoice Date
        invoice["invoice_date"] = self._parse_date(self._extract_field(fields, [
            "InvoiceDate", "DocumentDate", "Date", "Invoice Date"
        ]))
        
        # Due Date (not used in validation, but good to extract)
        # due_date = self._parse_date(self._extract_field(fields, ["DueDate", "PaymentDueDate"]))
        
        # Billing Period
        # Azure may provide InvoicePeriod or we need to extract from text
        period_start = self._extract_field(fields, [
            "InvoicePeriodStart", "BillingPeriodStart", "PeriodStart", "FromDate"
        ])
        period_end = self._extract_field(fields, [
            "InvoicePeriodEnd", "BillingPeriodEnd", "PeriodEnd", "ToDate"
        ])
        
        # If period not in fields, try to extract from tables or content
        if not period_start or not period_end:
            period_dates = self._extract_period_from_tables(full_data)
            if period_dates:
                period_start = period_dates.get("start")
                period_end = period_dates.get("end")
        
        # If still not found, try to extract from content (for British Gas format: "Bill period: 25 Nov 09 - 03 Mar 10")
        if not period_start or not period_end:
            content = full_data.get("content", "")
            if content:
                # British Gas format: "Bill period: 25 Nov 09 - 03 Mar 10"
                bg_period_patterns = [
                    r'bill\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',  # "Bill period: 25 Nov 09 - 03 Mar 10"
                    r'billing\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',  # "Billing period: 25 Nov 09 - 03 Mar 10"
                    r'period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',  # "Period: 25 Nov 09 - 03 Mar 10"
                ]
                
                for pattern in bg_period_patterns:
                    period_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                    if period_match:
                        period_start = period_match.group(1).strip()
                        period_end = period_match.group(2).strip()
                        logger.info(f"Found billing period in content: {period_start} to {period_end}")
                        break
        
        invoice["billing_period_start"] = self._parse_date(period_start)
        invoice["billing_period_end"] = self._parse_date(period_end)
        
        # If still no period, use invoice date as fallback
        if not invoice["billing_period_start"] and invoice["invoice_date"]:
            invoice["billing_period_start"] = invoice["invoice_date"]
        if not invoice["billing_period_end"] and invoice["invoice_date"]:
            invoice["billing_period_end"] = invoice["invoice_date"]
        
        # If still no invoice number, generate one from bill date (for British Gas)
        if not invoice["invoice_number"] and invoice["invoice_date"]:
            # Use format: BG-YYYY-MM-DD
            date_str = invoice["invoice_date"].strftime("%Y-%m-%d") if isinstance(invoice["invoice_date"], date) else str(invoice["invoice_date"])
            invoice["invoice_number"] = f"BG-{date_str}"
            logger.info(f"Generated invoice number from date: {invoice['invoice_number']}")
        
        # Amounts
        # Azure provides: Total, SubTotal, AmountDue, TaxTotal, etc.
        total = self._extract_field(fields, [
            "AmountDue", "Total", "InvoiceTotal", "TotalAmount", "Amount"
        ])
        invoice["gross_amount"] = self._parse_decimal(total)
        
        subtotal = self._extract_field(fields, [
            "SubTotal", "NetAmount", "AmountBeforeTax"
        ])
        invoice["net_amount"] = self._parse_decimal(subtotal)
        
        vat = self._extract_field(fields, [
            "TotalTax", "VAT", "Tax", "VATAmount", "TaxAmount"
        ])
        invoice["vat_amount"] = self._parse_decimal(vat)
        
        # If gross_amount not found, calculate from net + VAT
        if not invoice["gross_amount"] and invoice["net_amount"]:
            vat_amount = invoice["vat_amount"] or Decimal("0")
            invoice["gross_amount"] = invoice["net_amount"] + vat_amount
        
        # Currency
        currency = self._extract_field(fields, ["Currency", "CurrencyCode"])
        if currency:
            invoice["currency"] = str(currency).upper()[:3]  # Limit to 3 chars
        
        # Supplier Account Number (REQUIRED - separate from unit_id)
        # Try multiple field names that Azure might use
        account_number = self._extract_field(fields, [
            "CustomerAccountNumber", "AccountNumber", "Account", "CustomerNumber",
            "CustomerAccount", "AccountNo", "Account Number",
            "CustomerReferenceNumber", "CustomerReference", "ReferenceNumber", "Reference"
        ])
        
        if account_number:
            # Clean up account number (remove spaces, keep alphanumeric)
            account_number = self._clean_text(account_number)
            # Normalize account number for consistent matching
            account_str = normalize_account_number(account_number)
            logger.info(f"Found account number in Azure fields: {account_str}")
            invoice["supplier_account_number"] = account_str
        else:
            # If not found in fields, try to extract from content/text
            # Check content for account number patterns (E.ON format: "Your account number: 0123 4567 89")
            content = full_data.get("content", "")
            
            # Log a sample of content for debugging
            if content:
                content_sample = content[:500] if len(content) > 500 else content
                logger.info(f"Searching for account number in content (sample): {content_sample[:200]}...")
                
                # Look for patterns like:
                # "Your account number: 0123 4567 89"
                # "Account number: 0123 4567 89"
                # "Account: 0123456789"
                # "Customer reference number: 1234 1234 1234" (British Gas)
                account_patterns = [
                    r'(?:your\s+)?account\s+number[\s:]+([0-9\s-]{6,})',  # "Your account number: 0123 4567 89"
                    r'account\s+number[\s:]+([0-9\s-]{6,})',  # "Account number: 0123 4567 89"
                    r'account[\s:]+([0-9\s-]{6,})',  # "Account: 0123456789"
                    r'customer\s+account[\s:]+([0-9\s-]{6,})',  # "Customer account: 0123 4567 89"
                    r'account\s+no[\s:\.]+([0-9\s-]{6,})',  # "Account no: 0123 4567 89"
                    r'customer\s+reference\s+number[\s:]+([0-9\s-]{6,})',  # "Customer reference number: 1234 1234 1234" (British Gas)
                    r'customer\s+reference[\s:]+([0-9\s-]{6,})',  # "Customer reference: 1234 1234 1234"
                    r'reference\s+number[\s:]+([0-9\s-]{6,})',  # "Reference number: 1234 1234 1234"
                ]
                
                for pattern in account_patterns:
                    account_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                    if account_match:
                        account_str = account_match.group(1).strip()
                        # Clean up (remove extra spaces, keep digits and hyphens)
                        account_str = self._clean_text(account_str)  # Use cleaning method
                        if account_str:
                            digits_only = account_str.replace(' ', '').replace('-', '')
                            if len(digits_only) >= 6:  # At least 6 digits
                                account_str = self._clean_text(account_str)  # Clean again to remove any newlines
                                logger.info(f"Found account number in content: {account_str}")
                                # Normalize account number for consistent matching
                                invoice["supplier_account_number"] = normalize_account_number(account_str)
                                break
                
                # If not found, try multi-line patterns (account number on next line)
                # E.ON format: "Your account number\n0123 4567 89"
                # Opus format: "Your account number\n[text]\n495174" or "Your account number\n495174\n2"
                if not invoice.get("supplier_account_number"):
                    # First try Opus format: "Your account number" followed by account number (may have text in between)
                    # Pattern: "Your account number" then skip up to 2 lines, then find digits
                    opus_patterns = [
                        r'(?:your\s+)?account\s+number\s*\n(?:[^\n]*\n){0,2}\s*([0-9]{6,})',  # "Your account number\n[optional text]\n495174"
                        r'(?:your\s+)?account\s+number\s*\n\s*([0-9]+)\s*\n\s*([0-9]+)',  # "Your account number\n495174\n2"
                        r'account\s+number\s*\n(?:[^\n]*\n){0,2}\s*([0-9]{6,})',  # "Account number\n[optional text]\n495174"
                    ]
                    
                    for pattern in opus_patterns:
                        account_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                        if account_match:
                            # Handle Opus format: "Your account number\n495174\n2" (two groups)
                            if len(account_match.groups()) == 2:
                                account_str = account_match.group(1) + account_match.group(2)  # Combine: "495174" + "2" = "4951742"
                            else:
                                account_str = account_match.group(1).strip()
                            
                            account_str = self._clean_text(account_str, remove_all_spaces=True)  # Remove all spaces
                            if account_str:
                                digits_only = account_str.replace('-', '')  # Already no spaces
                                if len(digits_only) >= 6:
                                    logger.info(f"Found account number in content (Opus multi-line format): {account_str}")
                                    # Normalize account number for consistent matching
                                    invoice["supplier_account_number"] = normalize_account_number(account_str)
                                    break
                    
                    # If Opus patterns didn't match, try other multiline patterns
                    if not invoice.get("supplier_account_number"):
                        multiline_patterns = [
                            r'(?:your\s+)?account\s+number\s*\n\s*([0-9]{4}\s+[0-9]{4}\s+[0-9]{2})',  # "Your account number\n0123 4567 89"
                            r'account\s+number\s*\n\s*([0-9]{4}\s+[0-9]{4}\s+[0-9]{2})',  # "Account number\n0123 4567 89"
                            r'(?:your\s+)?account\s+number\s*\n\s*([0-9\s-]{8,15})',  # More flexible pattern
                        ]
                        
                        for pattern in multiline_patterns:
                            account_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                            if account_match:
                                account_str = account_match.group(1).strip()
                                account_str = self._clean_text(account_str, remove_all_spaces=True)  # Remove all spaces
                                if account_str:
                                    digits_only = account_str.replace('-', '')  # Already no spaces
                                    if len(digits_only) >= 6:
                                        logger.info(f"Found account number in content (multi-line): {account_str}")
                                        # Normalize account number for consistent matching
                                        invoice["supplier_account_number"] = normalize_account_number(account_str)
                                        break
                    
                    # If still not found, find "account number" or "customer reference" keyword and look for digits nearby
                    if not invoice.get("supplier_account_number"):
                        # Try "account number" first
                        account_keyword_match = re.search(
                            r'(?:your\s+)?account\s+number',
                            content,
                            re.IGNORECASE | re.MULTILINE
                        )
                        
                        # If not found, try "customer reference number" (British Gas)
                        if not account_keyword_match:
                            account_keyword_match = re.search(
                                r'customer\s+reference\s+number',
                                content,
                                re.IGNORECASE | re.MULTILINE
                            )
                        if account_keyword_match:
                            # Get text after "account number" (next 200 chars)
                            start_pos = account_keyword_match.end()
                            context = content[start_pos:start_pos + 200]
                            # Look for E.ON format: "0123 4567 89" (4 digits, space, 4 digits, space, 2 digits)
                            digit_match = re.search(r'([0-9]{4}\s+[0-9]{4}\s+[0-9]{2})', context)
                            if digit_match:
                                account_str = digit_match.group(1).strip()
                                logger.info(f"Found account number near keyword: {account_str}")
                                # Normalize account number for consistent matching
                                invoice["supplier_account_number"] = normalize_account_number(account_str)
                            else:
                                # Try any sequence of 8-15 digits with spaces
                                digit_match = re.search(r'([0-9\s]{8,15})', context)
                                if digit_match:
                                    potential_account = digit_match.group(1).strip()
                                    potential_account = self._clean_text(potential_account, remove_all_spaces=True)  # Remove all spaces
                                    if potential_account:
                                        digits_only = potential_account.replace('-', '')  # Already no spaces
                                        if 8 <= len(digits_only) <= 15:
                                            logger.info(f"Found potential account number: {potential_account}")
                                            # Normalize account number for consistent matching
                                            invoice["supplier_account_number"] = normalize_account_number(potential_account)
                
                # If still not found, check tables for account number
                if not invoice.get("supplier_account_number"):
                    tables = full_data.get("tables", [])
                    logger.info(f"Searching {len(tables)} tables for account number")
                    for table_idx, table in enumerate(tables):
                        cells = table.get("cells", [])
                        for cell in cells:
                            cell_content = cell.get("content", "")
                            if cell_content:
                                # Look for account number patterns in table cells
                                for pattern in account_patterns:
                                    account_match = re.search(pattern, cell_content, re.IGNORECASE)
                                    if account_match:
                                        account_str = account_match.group(1).strip()
                                        account_str = self._clean_text(account_str, remove_all_spaces=True)  # Remove all spaces
                                        if account_str:
                                            digits_only = account_str.replace('-', '')  # Already no spaces
                                            if len(digits_only) >= 6:
                                                logger.info(f"Found account number in table {table_idx}: {account_str}")
                                                # Normalize account number for consistent matching
                                                invoice["supplier_account_number"] = normalize_account_number(account_str)
                                                break
                                if invoice.get("supplier_account_number"):
                                    break
                            if invoice.get("supplier_account_number"):
                                break
                        if invoice.get("supplier_account_number"):
                            break
                
                # Last resort: search for any sequence of digits that looks like an account number
                if not invoice.get("supplier_account_number") and content:
                    # Look for patterns like "0123 4567 89" (spaces between groups of digits)
                    # This matches E.ON's format
                    account_match = re.search(
                        r'(?:account|account\s+number|account\s+no)[\s:\.]*([0-9]{4}\s+[0-9]{4}\s+[0-9]{2})',
                        content,
                        re.IGNORECASE | re.MULTILINE
                    )
                    if account_match:
                        account_str = account_match.group(1).strip()
                        logger.info(f"Found account number using digit pattern: {account_str}")
                        invoice["supplier_account_number"] = account_str
                    else:
                        # Try to find any 10-digit number near "account" keyword
                        account_context = re.search(
                            r'(?:account|account\s+number)[\s:\.]*([0-9\s]{8,15})',
                            content,
                            re.IGNORECASE | re.MULTILINE
                        )
                        if account_context:
                            potential_account = account_context.group(1).strip()
                            potential_account = self._clean_text(potential_account, remove_all_spaces=True)  # Remove all spaces
                            if potential_account:
                                digits_only = potential_account.replace('-', '')  # Already no spaces
                                if 8 <= len(digits_only) <= 15:  # Reasonable account number length
                                    logger.info(f"Found potential account number: {potential_account}")
                                    # Normalize account number for consistent matching
                                    invoice["supplier_account_number"] = normalize_account_number(potential_account)
            
            # If still not found, try British Gas specific pattern
            if not invoice.get("supplier_account_number") and content:
                # British Gas uses "Customer reference number" prominently
                # Pattern: "Customer reference number" followed by digits like "1234 1234 1234"
                british_gas_patterns = [
                    r'customer\s+reference\s+number[\s:]+([0-9]{4}\s+[0-9]{4}\s+[0-9]{4})',  # "1234 1234 1234"
                    r'customer\s+reference\s+number[\s:]+([0-9\s]{10,20})',  # More flexible
                    r'reference\s+number[\s:]+([0-9]{4}\s+[0-9]{4}\s+[0-9]{4})',  # "Reference number: 1234 1234 1234"
                ]
                
                for pattern in british_gas_patterns:
                    ref_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                    if ref_match:
                        ref_str = self._clean_text(ref_match.group(1), remove_all_spaces=False)  # Keep spaces for British Gas format "1234 1234 1234"
                        if ref_str:
                            digits_only = ref_str.replace(' ', '').replace('-', '')
                            if len(digits_only) >= 8:
                                logger.info(f"Found customer reference number (British Gas pattern): {ref_str}")
                                # Normalize account number for consistent matching
                                invoice["supplier_account_number"] = normalize_account_number(ref_str)
                                break
            
            # If still not found, log and leave as None - validation will catch it
            if not invoice.get("supplier_account_number"):
                logger.warning("Could not extract supplier_account_number from PDF. Content available: " + str(bool(content)))
                if content:
                    # Log a larger sample to help debug
                    logger.warning(f"Content sample (first 2000 chars): {content[:2000]}")
                invoice["supplier_account_number"] = None
        
        # Address and Unit ID
        # Extract both service/supply address (where utility is consumed) and customer address (where bill is sent)
        # For commercial real estate, we need the service address to match to units
        # But sometimes they're the same, so we'll try both
        
        content = full_data.get("content", "")
        
        # Priority 1: Extract supply/service address from content (most reliable)
        # British Gas: "Supply address: 86 EDLESTONE ROAD..."
        # E.ON: "For electricity supplied to Street, City..."
        # Opus: "For: Car Park Deer Park Road..."
        supply_address = None
        if content:
            # British Gas format: "Supply address: ..."
            supply_match = re.search(
                r'supply\s+address[\s:]+([^\n]+(?:\n[^\n]+){0,2})',
                content,
                re.IGNORECASE | re.MULTILINE
            )
            if supply_match:
                supply_address = supply_match.group(1).strip()
                logger.info(f"Found supply address in content (British Gas format): {supply_address[:100]}")
            else:
                # E.ON format: "For electricity supplied to ..."
                eon_match = re.search(
                    r'for\s+electricity\s+supplied\s+to\s+([^\n]+(?:\n[^\n]+){0,2})',
                    content,
                    re.IGNORECASE | re.MULTILINE
                )
                if eon_match:
                    supply_address = eon_match.group(1).strip()
                    logger.info(f"Found service address in content (E.ON format): {supply_address[:100]}")
                else:
                    # Opus format: "For: ..." (service address)
                    opus_match = re.search(
                        r'for[\s:]+([^\n]+(?:\n[^\n]+){0,3})',
                        content,
                        re.IGNORECASE | re.MULTILINE
                    )
                    if opus_match:
                        # Check if it's actually a service address (not just "For enquiries...")
                        opus_addr = opus_match.group(1).strip()
                        if not any(word in opus_addr.lower()[:50] for word in ['enquiry', 'contact', 'call', 'email', 'visit']):
                            supply_address = opus_addr
                            logger.info(f"Found service address in content (Opus format): {supply_address[:100]}")
        
        # Priority 2: Extract from Azure fields
        # ServiceAddress = where utility is supplied (what we want)
        # CustomerAddress = where bill is sent (might be same or different)
        service_address_field = self._extract_field(fields, ["ServiceAddress", "BillingAddress"])
        customer_address_field = self._extract_field(fields, ["CustomerAddress", "Address"])
        
        # Use supply address from content if found, otherwise try service address from fields
        # Fall back to customer address if neither found (sometimes they're the same location)
        final_address = supply_address
        if not final_address and service_address_field:
            final_address = service_address_field
            logger.info("Using ServiceAddress from Azure fields")
        elif not final_address and customer_address_field:
            final_address = customer_address_field
            logger.info("Using CustomerAddress from Azure fields (fallback - may be same as service address)")
        
        customer_address = final_address
        
        # Store full address
        if customer_address:
            if isinstance(customer_address, dict):
                # Address object - combine into string
                address_parts = []
                if customer_address.get("street_address"):
                    address_parts.append(str(customer_address.get("street_address")))
                if customer_address.get("city"):
                    address_parts.append(str(customer_address.get("city")))
                if customer_address.get("postal_code"):
                    address_parts.append(str(customer_address.get("postal_code")))
                invoice["address"] = ", ".join(address_parts) if address_parts else None
            else:
                invoice["address"] = str(customer_address).strip()
        else:
            # Try to extract address from content if not in fields
            # This is a fallback - we already tried above, but this handles edge cases
            if content:
                # Try all the same patterns again as fallback
                supply_match = re.search(
                    r'supply\s+address[\s:]+([^\n]+(?:\n[^\n]+){0,2})',
                    content,
                    re.IGNORECASE | re.MULTILINE
                )
                if supply_match:
                    invoice["address"] = supply_match.group(1).strip()
                    logger.info(f"Extracted supply address from content (fallback): {invoice['address'][:100]}")
                else:
                    # Try E.ON format
                    eon_match = re.search(
                        r'for\s+electricity\s+supplied\s+to\s+([^\n]+(?:\n[^\n]+){0,2})',
                        content,
                        re.IGNORECASE | re.MULTILINE
                    )
                    if eon_match:
                        invoice["address"] = eon_match.group(1).strip()
                        logger.info(f"Extracted service address from content (E.ON fallback): {invoice['address'][:100]}")
                    else:
                        # Try Opus format
                        opus_match = re.search(
                            r'for[\s:]+([^\n]+(?:\n[^\n]+){0,3})',
                            content,
                            re.IGNORECASE | re.MULTILINE
                        )
                        if opus_match:
                            opus_addr = opus_match.group(1).strip()
                            if not any(word in opus_addr.lower()[:50] for word in ['enquiry', 'contact', 'call', 'email', 'visit']):
                                invoice["address"] = opus_addr
                                logger.info(f"Extracted service address from content (Opus fallback): {invoice['address'][:100]}")
                        else:
                            # Final fallback: Look for generic address patterns
                            address_match = re.search(
                                r'(?:Bill\s+to|Service\s+address)[\s:]+([^\n]+(?:\n[^\n]+){0,3})',
                                content,
                                re.IGNORECASE | re.MULTILINE
                            )
                            if address_match:
                                invoice["address"] = address_match.group(1).strip()
                                logger.info(f"Extracted address from content (generic fallback): {invoice['address'][:100]}")
        
        # Extract unit_id from address (NOT postcode - prioritize actual unit identifiers)
        unit_id = self._extract_unit_id(customer_address, fields, invoice.get("address"))
        invoice["unit_id"] = unit_id
        
        # Utility Type
        # Try to detect from supplier name or invoice content
        utility_type = self._detect_utility_type(invoice["supplier_name"], full_data)
        invoice["utility_type"] = utility_type
        
        return invoice
    
    def _extract_field(self, fields: Dict[str, Any], possible_keys: List[str]) -> Optional[Any]:
        """
        Extract field value by trying multiple possible keys.
        
        Args:
            fields: Dictionary of extracted fields
            possible_keys: List of possible field names to try
        
        Returns:
            Field value or None
        """
        for key in possible_keys:
            if key in fields:
                field_data = fields[key]
                # Handle nested structure from Azure
                if isinstance(field_data, dict):
                    return field_data.get("value") or field_data.get("content")
                return field_data
        
        # Try case-insensitive search
        fields_lower = {k.lower(): v for k, v in fields.items()}
        for key in possible_keys:
            key_lower = key.lower()
            if key_lower in fields_lower:
                field_data = fields_lower[key_lower]
                if isinstance(field_data, dict):
                    return field_data.get("value") or field_data.get("content")
                return field_data
        
        return None
    
    def _parse_date(self, date_str: Any) -> Optional[date]:
        """
        Parse date string to date object.
        
        Args:
            date_str: Date string or date object
        
        Returns:
            date object or None
        """
        if date_str is None:
            return None
        
        if isinstance(date_str, date):
            return date_str
        
        if isinstance(date_str, datetime):
            return date_str.date()
        
        # Try to parse string
        date_str = str(date_str).strip()
        if not date_str or date_str.lower() in ["none", "null", ""]:
            return None
        
        # Common date formats
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d.%m.%Y",
            "%d %B %Y",
            "%d %b %Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %b %y",  # E.ON format: "08 Jan 14"
            "%d %B %y",  # "08 January 14"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # Try regex for UK dates (DD/MM/YYYY)
        uk_date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', date_str)
        if uk_date_match:
            try:
                day, month, year = uk_date_match.groups()
                return date(int(year), int(month), int(day))
            except ValueError:
                pass
        
        # Try E.ON format: "08 Jan 14" or "18 Feb 14"
        eon_date_match = re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2})', date_str)
        if eon_date_match:
            try:
                day, month_str, year_str = eon_date_match.groups()
                # Convert 2-digit year to 4-digit (assume 2000-2099)
                year = 2000 + int(year_str) if int(year_str) < 50 else 1900 + int(year_str)
                # Parse month abbreviation
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                month = month_map.get(month_str.lower())
                if month:
                    return date(year, month, int(day))
            except (ValueError, KeyError):
                pass
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """
        Parse value to Decimal.
        
        Args:
            value: Value to parse (string, number, etc.)
        
        Returns:
            Decimal or None
        """
        if value is None:
            return None
        
        if isinstance(value, Decimal):
            return value
        
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        
        # Try to parse string
        value_str = str(value).strip()
        if not value_str or value_str.lower() in ["none", "null", ""]:
            return None
        
        # Remove currency symbols and commas
        value_str = re.sub(r'[£$€,\s]', '', value_str)
        
        try:
            return Decimal(value_str)
        except (ValueError, TypeError):
            logger.warning(f"Could not parse decimal: {value}")
            return None
    
    def _extract_period_from_tables(self, full_data: Dict[str, Any]) -> Optional[Dict[str, Optional[str]]]:
        """
        Extract billing period from tables in the PDF.
        
        Args:
            full_data: Full extraction data including tables
        
        Returns:
            Dictionary with 'start' and 'end' date strings or None
        """
        tables = full_data.get("tables", [])
        
        for table in tables:
            cells = table.get("cells", [])
            
            # Look for period-related keywords
            period_keywords = ["period", "billing", "from", "to", "start", "end", "date"]
            
            # First, try to find a cell with date range pattern like "08 Jan 14 to 18 Feb 14"
            for cell in cells:
                cell_content = cell.get("content", "")
                if not cell_content:
                    continue
                
                # Check for date range patterns like "08 Jan 14 to 18 Feb 14"
                date_range_match = re.search(
                    r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s+to\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',
                    cell_content,
                    re.IGNORECASE
                )
                if date_range_match:
                    start_str = date_range_match.group(1)
                    end_str = date_range_match.group(2)
                    start_date = self._parse_date(start_str)
                    end_date = self._parse_date(end_str)
                    if start_date and end_date:
                        return {"start": str(start_date), "end": str(end_date)}
            
            # Also check entire row text for date ranges
            for cell in cells:
                content = cell.get("content", "").lower() if cell.get("content") else ""
                
                # Check if cell contains period keywords
                if any(keyword in content for keyword in period_keywords):
                    # Get all cells in same row
                    row_idx = cell.get("row_index")
                    row_cells = [c for c in cells if c.get("row_index") == row_idx]
                    row_text = " ".join([c.get("content", "") for c in row_cells])
                    
                    # Try to find date range in row text
                    date_range_match = re.search(
                        r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s+to\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',
                        row_text,
                        re.IGNORECASE
                    )
                    if date_range_match:
                        start_str = date_range_match.group(1)
                        end_str = date_range_match.group(2)
                        start_date = self._parse_date(start_str)
                        end_date = self._parse_date(end_str)
                        if start_date and end_date:
                            return {"start": str(start_date), "end": str(end_date)}
                    
                    # Try to find dates in nearby cells
                    col_idx = cell.get("column_index")
                    dates_found = []
                    for other_cell in cells:
                        if (other_cell.get("row_index") == row_idx and 
                            other_cell.get("column_index") != col_idx):
                            cell_content = other_cell.get("content", "")
                            parsed_date = self._parse_date(cell_content)
                            if parsed_date:
                                dates_found.append(parsed_date)
                    
                    if len(dates_found) >= 2:
                        # Sort dates and return earliest as start, latest as end
                        dates_found.sort()
                        return {
                            "start": str(dates_found[0]),
                            "end": str(dates_found[-1])
                        }
        
        # Also check content field for date ranges
        content = full_data.get("content", "")
        if content:
            # Look for British Gas format: "Bill period: 25 Nov 09 - 03 Mar 10"
            bg_period_patterns = [
                r'bill\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',  # "Bill period: 25 Nov 09 - 03 Mar 10"
                r'billing\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',  # "Billing period: 25 Nov 09 - 03 Mar 10"
            ]
            
            for pattern in bg_period_patterns:
                period_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if period_match:
                    start_str = period_match.group(1).strip()
                    end_str = period_match.group(2).strip()
                    start_date = self._parse_date(start_str)
                    end_date = self._parse_date(end_str)
                    if start_date and end_date:
                        logger.info(f"Found billing period in content (British Gas format): {start_str} to {end_str}")
                        return {"start": str(start_date), "end": str(end_date)}
            
            # Look for Opus format: "Invoice period: 01 April 2014 to 07 April 2014"
            opus_period_patterns = [
                r'invoice\s+period[\s:]+(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s+to\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # "Invoice period: 01 April 2014 to 07 April 2014"
                r'billing\s+period[\s:]+(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s+to\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # "Billing period: 01 April 2014 to 07 April 2014"
            ]
            
            for pattern in opus_period_patterns:
                period_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if period_match:
                    start_str = period_match.group(1).strip()
                    end_str = period_match.group(2).strip()
                    start_date = self._parse_date(start_str)
                    end_date = self._parse_date(end_str)
                    if start_date and end_date:
                        logger.info(f"Found billing period in content (Opus format): {start_str} to {end_str}")
                        return {"start": str(start_date), "end": str(end_date)}
            
            # Look for E.ON format: "08 Jan 14 to 18 Feb 14"
            date_range_match = re.search(
                r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s+to\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',
                content,
                re.IGNORECASE
            )
            if date_range_match:
                start_str = date_range_match.group(1)
                end_str = date_range_match.group(2)
                start_date = self._parse_date(start_str)
                end_date = self._parse_date(end_str)
                if start_date and end_date:
                    return {"start": str(start_date), "end": str(end_date)}
            
            # Also try generic date range with dash: "25 Nov 09 - 03 Mar 10" (without "Bill period" prefix)
            generic_dash_match = re.search(
                r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',
                content,
                re.IGNORECASE
            )
            if generic_dash_match:
                start_str = generic_dash_match.group(1).strip()
                end_str = generic_dash_match.group(2).strip()
                start_date = self._parse_date(start_str)
                end_date = self._parse_date(end_str)
                if start_date and end_date:
                    logger.info(f"Found billing period in content (generic dash format): {start_str} to {end_str}")
                    return {"start": str(start_date), "end": str(end_date)}
        
        return None
    
    def _extract_unit_id(self, address: Any, fields: Dict[str, Any], address_str: Optional[str] = None) -> Optional[str]:
        """
        Extract unit_id from address (NOT from account number - that's extracted separately).
        Prioritizes actual unit identifiers (Unit 1, Shop 5, OFFICE-101) over postcode.
        
        Args:
            address: Address field from extraction
            fields: All extracted fields (account number already extracted separately)
            address_str: Optional pre-formatted address string
        
        Returns:
            Unit ID string or None (do NOT use postcode as default)
        """
        # NOTE: Account number is now extracted separately as supplier_account_number
        # Unit ID should come from property/unit references in the address
        
        # Get address string
        if address_str:
            address_text = address_str
        elif address:
            if isinstance(address, dict):
                # Address object
                address_text = " ".join([
                    str(address.get("street_address", "")),
                    str(address.get("city", "")),
                    str(address.get("postal_code", ""))
                ])
            else:
                address_text = str(address)
        else:
            return None
        
        # PRIORITY 1: Try to find actual unit/property references in address
        # Look for patterns like "Unit 1", "Shop 5", "OFFICE-101", etc.
        unit_patterns = [
            r'(?:Unit|Shop|Office|Suite|Flat|Apartment)\s*([A-Z0-9-]+)',  # "Unit 1", "Shop 5", "OFFICE-101"
            r'([A-Z]{2,}-\d{3,})',  # Pattern like SHOP-001, OFFICE-101
            r'(\d{1,3}[A-Z]\d{1,3})',  # Pattern like 1A2
            r'(?:Unit|Shop|Office)\s*(\d+)',  # "Unit 1", "Shop 5"
        ]
        for pattern in unit_patterns:
            match = re.search(pattern, address_text, re.IGNORECASE)
            if match:
                unit_id = match.group(1).upper().strip()
                if unit_id and len(unit_id) <= 50:  # Reasonable length
                    logger.info(f"Found unit_id in address: {unit_id}")
                    return unit_id
        
        # PRIORITY 2: Use first line of address if it looks like a unit reference
        lines = address_text.split("\n")
        if lines:
            first_line = lines[0].strip()
            # If first line looks like a unit ID (short, alphanumeric, not a full address)
            if (len(first_line) <= 20 and 
                re.match(r'^[A-Z0-9\s-]+$', first_line, re.IGNORECASE) and
                not re.search(r'\d{5,}', first_line)):  # Not a postcode (5+ digits)
                logger.info(f"Using first line as unit_id: {first_line}")
                return first_line[:50]  # Limit length
        
        # PRIORITY 3: Do NOT use postcode as unit_id - return None instead
        # Postcode is not a unit identifier, it's a location identifier
        # If no unit identifier is found, return None (user can map manually)
        logger.info("No unit identifier found in address - returning None (user can map manually)")
        return None
    
    def _detect_utility_type(self, supplier_name: Optional[str], full_data: Dict[str, Any]) -> str:
        """
        Detect utility type from supplier name or invoice content.
        
        Args:
            supplier_name: Supplier name
            full_data: Full extraction data
        
        Returns:
            Utility type string (default: "Electricity")
        """
        if supplier_name:
            supplier_lower = supplier_name.lower()
            
            # Check for gas suppliers
            if "gas" in supplier_lower or "british gas" in supplier_lower:
                return "Gas"
            
            # Check content for utility type keywords
            content = full_data.get("content", "").lower()
            
            if "electricity" in content or "kwh" in content:
                return "Electricity"
            elif "gas" in content or "therm" in content or "m3" in content:
                return "Gas"
            elif "water" in content:
                return "Water"
        
        return "Electricity"  # Default


def normalize_pdf_invoice(extracted_data: Dict[str, Any], supplier_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to normalize PDF invoice data.
    
    Args:
        extracted_data: Dictionary from Azure Document Intelligence
        supplier_name: Optional supplier name for supplier-specific normalization
    
    Returns:
        List of normalized invoice dictionaries
    """
    normalizer = PDFNormalizer(supplier_name=supplier_name)
    return normalizer.normalize(extracted_data)



