"""
Account number normalization utility.

This module provides functions to normalize account numbers to ensure consistent
formatting between extracted account numbers and stored account mappings.
"""

import re
from typing import Optional, Tuple


def normalize_account_number(account_number: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalize an account number to ensure consistent matching.
    
    Args:
        account_number: The account number to normalize
        
    Returns:
        Tuple of (display_format, matching_format) where:
            - display_format: The formatted account number for display (with spaces)
            - matching_format: The normalized account number for matching (no spaces/dashes)
    """
    if not account_number:
        return None, None
        
    # Clean the account number (remove extra whitespace)
    account_str = account_number.strip()
    account_str = re.sub(r'\s+', ' ', account_str)
    
    # Keep original format for display
    display_format = account_str
    
    # Create normalized format for matching (no spaces or dashes)
    matching_format = account_str.replace(" ", "").replace("-", "")
    
    return display_format, matching_format