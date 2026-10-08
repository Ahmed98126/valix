"""Email service for sending emails using Resend."""

import os
import resend
from typing import Optional
import logging

from app.config import RESEND_API_KEY, RESEND_FROM_EMAIL, RESEND_FROM_NAME

logger = logging.getLogger(__name__)


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None
) -> bool:
    """Send an email using Resend.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Optional plain text body

    Returns:
        True if sent successfully, False otherwise
    """
    # Read fresh from env each call so restarts always pick up latest value
    api_key = os.getenv("RESEND_API_KEY", "") or RESEND_API_KEY
    from_email = os.getenv("RESEND_FROM_EMAIL", "") or RESEND_FROM_EMAIL
    from_name = os.getenv("RESEND_FROM_NAME", "") or RESEND_FROM_NAME

    if not api_key:
        logger.warning("RESEND_API_KEY not configured. Email not sent.")
        return False

    try:
        resend.api_key = api_key

        from_address = (
            f"{from_name} <{from_email}>"
            if from_name
            else from_email
        )

        params: dict = {
            "from": from_address,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        if text_body:
            params["text"] = text_body

        response = resend.Emails.send(params)

        # Resend returns a dict with an "id" key on success
        if response and response.get("id"):
            logger.info(f"Email sent successfully to {to_email} (id: {response['id']})")
            return True
        else:
            logger.error(f"Failed to send email to {to_email}. Response: {response}")
            return False

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
        return False


def send_password_reset_email(
    to_email: str,
    reset_token: str,
    reset_url: str,
    user_name: Optional[str] = None
) -> bool:
    """Send password reset email.
    
    Args:
        to_email: User email address
        reset_token: Password reset token
        reset_url: Full URL for password reset (e.g., https://valixs.com/reset-password?token=...)
        user_name: Optional user name for personalization
    
    Returns:
        True if sent successfully, False otherwise
    """
    subject = "Reset Your Valix Password"
    
    # Create reset link
    reset_link = f"{reset_url}?token={reset_token}"
    
    # HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #000; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Valix</h1>
                <p>Password Reset Request</p>
            </div>
            <div class="content">
                <p>Hello{f' {user_name}' if user_name else ''},</p>
                
                <p>We received a request to reset your password for your Valix account.</p>
                
                <p>Click the button below to reset your password:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{reset_link}</p>
                
                <p><strong>This link will expire in 24 hours.</strong></p>
                
                <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                
                <p>Best regards,<br>The Valix Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    Hello{user_name if user_name else ''},
    
    We received a request to reset your password for your Valix account.
    
    Click this link to reset your password:
    {reset_link}
    
    This link will expire in 24 hours.
    
    If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
    
    Best regards,
    The Valix Team
    """
    
    return send_email(to_email, subject, html_body, text_body)


def send_welcome_email(
    to_email: str,
    user_name: Optional[str] = None,
    organization_name: Optional[str] = None,
    login_url: str = "https://valixs.com/login"
) -> bool:
    """Send welcome email after account creation.
    
    Args:
        to_email: User email address
        user_name: Optional user name for personalization
        organization_name: Optional organization name
        login_url: URL to login page
    
    Returns:
        True if sent successfully, False otherwise
    """
    subject = "Welcome to Valix! 🎉"
    
    # HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #000; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            .features {{ margin: 20px 0; }}
            .feature {{ margin: 10px 0; padding-left: 25px; position: relative; }}
            .feature:before {{ content: "✓"; position: absolute; left: 0; color: #10b981; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to Valix! 🎉</h1>
                <p>Your account has been created successfully</p>
            </div>
            <div class="content">
                <p>Hello{f' {user_name}' if user_name else ''},</p>
                
                <p>Thank you for signing up for Valix! We're excited to have you on board.</p>
                
                {f'<p>Your organization <strong>{organization_name}</strong> has been set up and is ready to use.</p>' if organization_name else ''}
                
                <p>You can now start using Valix to validate your invoices and manage your property data.</p>
                
                <div class="features">
                    <p><strong>What you can do:</strong></p>
                    <div class="feature">Upload and validate invoices</div>
                    <div class="feature">Manage units and leases</div>
                    <div class="feature">Track validation results</div>
                    <div class="feature">Export data and reports</div>
                </div>
                
                <div style="text-align: center;">
                    <a href="{login_url}" class="button">Get Started</a>
                </div>
                
                <p>If you have any questions, feel free to reach out to our support team.</p>
                
                <p>Best regards,<br>The Valix Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    Hello{user_name if user_name else ''},
    
    Thank you for signing up for Valix! We're excited to have you on board.
    
    {f'Your organization {organization_name} has been set up and is ready to use.' if organization_name else ''}
    
    You can now start using Valix to validate your invoices and manage your property data.
    
    Get started by logging in: {login_url}
    
    If you have any questions, feel free to reach out to our support team.
    
    Best regards,
    The Valix Team
    """
    
    return send_email(to_email, subject, html_body, text_body)


def send_email_verification_email(
    to_email: str,
    verification_token: str,
    verification_url: str,
    user_name: Optional[str] = None
) -> bool:
    """Send email verification email.
    
    Args:
        to_email: User email address
        verification_token: Email verification token
        verification_url: Base URL for verification (e.g., https://valixs.com/verify-email)
        user_name: Optional user name for personalization
    
    Returns:
        True if sent successfully, False otherwise
    """
    subject = "Verify Your Valix Email Address"
    
    # Create verification link
    verification_link = f"{verification_url}?token={verification_token}"
    
    # HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #000; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Valix</h1>
                <p>Verify Your Email Address</p>
            </div>
            <div class="content">
                <p>Hello{f' {user_name}' if user_name else ''},</p>
                
                <p>Thank you for signing up for Valix! To complete your registration, please verify your email address.</p>
                
                <p>Click the button below to verify your email:</p>
                
                <div style="text-align: center;">
                    <a href="{verification_link}" class="button">Verify Email Address</a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{verification_link}</p>
                
                <div class="warning">
                    <p><strong>Important:</strong> This verification link will expire in 48 hours.</p>
                    <p>If you don't verify your email, you may have limited access to your account.</p>
                </div>
                
                <p>If you didn't create a Valix account, please ignore this email.</p>
                
                <p>Best regards,<br>The Valix Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    Hello{user_name if user_name else ''},
    
    Thank you for signing up for Valix! To complete your registration, please verify your email address.
    
    Click this link to verify your email:
    {verification_link}
    
    This verification link will expire in 48 hours.
    
    If you didn't create a Valix account, please ignore this email.
    
    Best regards,
    The Valix Team
    """
    
    return send_email(to_email, subject, html_body, text_body)
