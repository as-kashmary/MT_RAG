"""
Email Service for Executive Portal.
Provides SMTP-based email sending functionality for admin invitations.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

from src.logging.logging import get_logger
logger = get_logger("email_service")

# Load environment variables from .env file
load_dotenv()


@dataclass
class EmailConfig:
    """SMTP email configuration from environment variables."""
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", "smtp.gmail.com"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    smtp_user: str = field(default_factory=lambda: os.getenv("SMTP_USER", ""))
    smtp_password: str = field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    from_email: str = field(default_factory=lambda: os.getenv("SMTP_FROM_EMAIL", ""))
    from_name: str = field(default_factory=lambda: os.getenv("SMTP_FROM_NAME", "MT-RAG System"))
    
    @property
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        configured = bool(self.smtp_user and self.smtp_password and self.from_email)
        if not configured:
            logger.warning(f"Email config check - User: '{self.smtp_user}', Password: {'*' * len(self.smtp_password) if self.smtp_password else 'empty'}, From: '{self.from_email}'")
        return configured


def get_email_config() -> EmailConfig:
    """Get email configuration from environment."""
    config = EmailConfig()
    logger.info(f"Email config loaded - Host: {config.smtp_host}, Port: {config.smtp_port}, User: {config.smtp_user}")
    return config


def send_admin_invite_email(
    to_email: str,
    admin_username: str,
    temp_password: str,
    company_name: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> bool:
    """
    Send admin invitation email with credentials.
    Uses the executive's email as sender if provided.
    
    Args:
        to_email: Admin's email address
        admin_username: The username for the admin account
        temp_password: Temporary password for first login
        company_name: Name of the company
        from_email: Executive's email to use as sender (optional)
        from_name: Executive's name to use as sender name (optional)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    config = get_email_config()
    
    if not config.is_configured:
        logger.warning("Email not configured. Skipping email send.")
        return False
    
    # Use executive's email as sender, fall back to config
    sender_email = from_email if from_email else config.from_email
    sender_name = from_name if from_name else config.from_name
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your {company_name} Admin Credentials"
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email
        
        # Plain text version
        text_content = f"""Hello {admin_username},

You have been invited to join {company_name} as an Admin on the MT-RAG System.

Your login credentials are:
Username: {admin_username}
Temporary Password: {temp_password}

Please login at your earliest convenience and change your password.

Best regards,
{company_name} Team
"""
        
        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #0ea5e9, #0284c7); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8fafc; padding: 30px; border: 1px solid #e2e8f0; }}
        .credentials {{ background: #1e293b; color: #f1f5f9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .credentials p {{ margin: 8px 0; }}
        .label {{ color: #94a3b8; font-size: 12px; }}
        .value {{ font-family: monospace; font-size: 16px; color: #38bdf8; }}
        .footer {{ background: #1e293b; color: #94a3b8; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">Welcome to {company_name}!</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">You've been invited as an Admin</p>
        </div>
        <div class="content">
            <p>Hello <strong>{admin_username}</strong>,</p>
            <p>You have been invited to join <strong>{company_name}</strong> as an Admin on the MT-RAG System.</p>
            
            <div class="credentials">
                <p class="label">USERNAME</p>
                <p class="value">{admin_username}</p>
                <p class="label" style="margin-top: 15px;">TEMPORARY PASSWORD</p>
                <p class="value">{temp_password}</p>
            </div>
            
            <p>Please login at your earliest convenience and change your password for security.</p>
            <p>Best regards,<br><strong>{company_name} Team</strong></p>
        </div>
        <div class="footer">
            This is an automated message from MT-RAG System. Please do not reply.
        </div>
    </div>
</body>
</html>
"""
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        # Send email
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            server.starttls()
            server.login(config.smtp_user, config.smtp_password)
            server.sendmail(config.from_email, to_email, msg.as_string())
        
        logger.info(f"Successfully sent admin invite email to: {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {str(e)}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send admin invite email: {str(e)}")
        return False
