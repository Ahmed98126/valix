"""Centralized error handling and user-friendly error messages."""

from typing import Dict, Optional
from fastapi import HTTPException


# User-friendly error messages
ERROR_MESSAGES = {
    # File upload errors
    "file_too_large": "The file is too large. Maximum size is {max_size}MB. Please split your file into smaller batches.",
    "invalid_file_type": "Invalid file type. Please upload Excel (.xlsx, .xls) or CSV files only.",
    "missing_columns": "Missing required columns: {missing}. Please check your file format. Available columns: {available}",
    "invalid_date_format": "Invalid date format in row {row}. Expected format: YYYY-MM-DD or DD/MM/YYYY. Found: {value}",
    "invalid_amount": "Invalid amount in row {row}. Expected a number. Found: {value}",
    
    # Data import errors
    "unit_not_found": "Unit '{unit_id}' not found. Please import units first before importing leases.",
    "duplicate_unit": "Unit '{unit_id}' already exists. Use the Data Management page to edit existing units.",
    "invalid_unit_id": "Invalid unit_id in row {row}: '{unit_id}'. Unit IDs must match existing units.",
    
    # Validation errors
    "validation_failed": "Validation failed for invoice {invoice_number}: {reason}",
    "duplicate_invoice": "Invoice {invoice_number} with amount £{amount} already exists in batch {batch}.",
    
    # Authentication errors
    "invalid_credentials": "Invalid email or password. Please try again.",
    "user_not_found": "User not found. Please check your email address.",
    "unauthorized": "You don't have permission to access this resource.",
    "tenant_required": "You must be associated with a tenant to perform this action.",
    "password_reset_invalid": "Invalid or expired password reset token. Please request a new one.",
    "password_reset_expired": "This password reset link has expired. Please request a new one.",
    "password_too_short": "Password must be at least 8 characters long.",
    "passwords_dont_match": "Passwords do not match. Please try again.",
    
    # Database errors
    "database_error": "A database error occurred. Please try again or contact support.",
    "connection_error": "Unable to connect to the database. Please try again later.",
    
    # General errors
    "unknown_error": "An unexpected error occurred. Please try again or contact support if the problem persists.",
    "processing_error": "Error processing your request: {details}",
}


def get_user_friendly_error(error_type: str, **kwargs) -> str:
    """
    Get a user-friendly error message.
    
    Args:
        error_type: Error type key from ERROR_MESSAGES
        **kwargs: Variables to format into the message
    
    Returns:
        Formatted error message
    """
    message_template = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["unknown_error"])
    try:
        return message_template.format(**kwargs)
    except KeyError:
        # If formatting fails, return the template as-is
        return message_template


def format_validation_errors(errors: list) -> str:
    """
    Format validation errors into a user-friendly message.
    
    Args:
        errors: List of error dictionaries or strings
    
    Returns:
        Formatted error message
    """
    if not errors:
        return "Validation completed with no errors."
    
    if len(errors) == 1:
        error = errors[0]
        if isinstance(error, dict):
            error_type = error.get("type", "unknown_error")
            return get_user_friendly_error(error_type, **error)
        return str(error)
    
    # Multiple errors
    error_summary = f"Found {len(errors)} issues:\n"
    for i, error in enumerate(errors[:10], 1):  # Show first 10
        if isinstance(error, dict):
            error_type = error.get("type", "unknown_error")
            error_summary += f"{i}. {get_user_friendly_error(error_type, **error)}\n"
        else:
            error_summary += f"{i}. {str(error)}\n"
    
    if len(errors) > 10:
        error_summary += f"... and {len(errors) - 10} more issues."
    
    return error_summary


def create_error_response(error_type: str, status_code: int = 400, **kwargs) -> HTTPException:
    """
    Create an HTTPException with a user-friendly error message.
    
    Args:
        error_type: Error type key
        status_code: HTTP status code
        **kwargs: Variables for error message
    
    Returns:
        HTTPException with formatted message
    """
    message = get_user_friendly_error(error_type, **kwargs)
    return HTTPException(status_code=status_code, detail=message)


