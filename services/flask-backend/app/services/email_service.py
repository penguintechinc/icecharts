"""Email service with multi-provider support for IceCharts."""

import logging
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import Config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with multiple provider support."""

    @staticmethod
    def get_email_provider() -> str:
        """
        Get configured email provider from system settings.

        Returns:
            Provider name (sendmail, smtp, sendgrid, aws_ses, mailgun, gmail)
        """
        # Import here to avoid circular dependency
        from app.services.system_settings_service import SystemSettingsService

        provider = SystemSettingsService.get_setting("email_provider", "sendmail")
        return provider

    @staticmethod
    def send_email(
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send email using configured provider.

        Args:
            to: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (optional, will be extracted from HTML if not provided)
            from_email: Sender email (defaults to system setting)
            from_name: Sender name (defaults to system setting)

        Returns:
            True if email sent successfully, False otherwise
        """
        # Import here to avoid circular dependency
        from app.services.system_settings_service import SystemSettingsService

        try:
            provider = EmailService.get_email_provider()

            # Get default from email and name if not provided
            if not from_email:
                from_email = SystemSettingsService.get_setting(
                    "email_from", Config.EMAIL_FROM
                )
            if not from_name:
                from_name = SystemSettingsService.get_setting(
                    "email_from_name", Config.EMAIL_FROM_NAME
                )

            # Generate plain text version if not provided
            if not body_text:
                # Simple HTML stripping (in production, use html2text library)
                import re

                body_text = re.sub(r"<[^>]+>", "", body_html)

            # Dispatch to appropriate provider
            if provider == "smtp":
                return EmailService._send_via_smtp(
                    to, subject, body_html, body_text, from_email, from_name
                )
            elif provider == "sendgrid":
                return EmailService._send_via_sendgrid(
                    to, subject, body_html, body_text, from_email, from_name
                )
            elif provider == "aws_ses":
                return EmailService._send_via_aws_ses(
                    to, subject, body_html, body_text, from_email, from_name
                )
            elif provider == "mailgun":
                return EmailService._send_via_mailgun(
                    to, subject, body_html, body_text, from_email, from_name
                )
            elif provider == "gmail":
                return EmailService._send_via_gmail(
                    to, subject, body_html, body_text, from_email, from_name
                )
            else:
                # Default to sendmail
                return EmailService._send_via_sendmail(
                    to, subject, body_html, body_text, from_email, from_name
                )

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False

    @staticmethod
    def _send_via_smtp(
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        from_email: str,
        from_name: str,
    ) -> bool:
        """Send email via SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = to

            # Attach parts
            part1 = MIMEText(body_text, "plain")
            part2 = MIMEText(body_html, "html")
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
                if Config.SMTP_USE_TLS:
                    server.starttls()
                if Config.SMTP_USER and Config.SMTP_PASSWORD:
                    server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email sent via SMTP to {to}")
            return True

        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}")
            return False

    @staticmethod
    def _send_via_sendgrid(
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        from_email: str,
        from_name: str,
    ) -> bool:
        """Send email via SendGrid."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Content, Email, Mail, To

            message = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to),
                subject=subject,
                plain_text_content=Content("text/plain", body_text),
                html_content=Content("text/html", body_html),
            )

            sg = SendGridAPIClient(Config.SENDGRID_API_KEY)
            response = sg.send(message)

            logger.info(f"Email sent via SendGrid to {to}, status: {response.status_code}")
            return response.status_code in (200, 201, 202)

        except ImportError:
            logger.error("SendGrid library not installed. Install with: pip install sendgrid")
            return False
        except Exception as e:
            logger.error(f"SendGrid send failed: {str(e)}")
            return False

    @staticmethod
    def _send_via_aws_ses(
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        from_email: str,
        from_name: str,
    ) -> bool:
        """Send email via AWS SES."""
        try:
            import boto3

            client = boto3.client(
                "ses",
                region_name=Config.AWS_SES_REGION,
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            )

            response = client.send_email(
                Source=f"{from_name} <{from_email}>",
                Destination={"ToAddresses": [to]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": body_text, "Charset": "UTF-8"},
                        "Html": {"Data": body_html, "Charset": "UTF-8"},
                    },
                },
            )

            logger.info(f"Email sent via AWS SES to {to}, message_id: {response['MessageId']}")
            return True

        except ImportError:
            logger.error("Boto3 library not installed. Install with: pip install boto3")
            return False
        except Exception as e:
            logger.error(f"AWS SES send failed: {str(e)}")
            return False

    @staticmethod
    def _send_via_mailgun(
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        from_email: str,
        from_name: str,
    ) -> bool:
        """Send email via Mailgun."""
        try:
            import requests

            response = requests.post(
                f"https://api.mailgun.net/v3/{Config.MAILGUN_DOMAIN}/messages",
                auth=("api", Config.MAILGUN_API_KEY),
                data={
                    "from": f"{from_name} <{from_email}>",
                    "to": to,
                    "subject": subject,
                    "text": body_text,
                    "html": body_html,
                },
            )

            logger.info(f"Email sent via Mailgun to {to}, status: {response.status_code}")
            return response.status_code == 200

        except ImportError:
            logger.error("Requests library not installed. Install with: pip install requests")
            return False
        except Exception as e:
            logger.error(f"Mailgun send failed: {str(e)}")
            return False

    @staticmethod
    def _send_via_gmail(
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        from_email: str,
        from_name: str,
    ) -> bool:
        """Send email via Gmail SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = to

            # Attach parts
            part1 = MIMEText(body_text, "plain")
            part2 = MIMEText(body_html, "html")
            msg.attach(part1)
            msg.attach(part2)

            # Send via Gmail SMTP
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(Config.GMAIL_USER, Config.GMAIL_APP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email sent via Gmail to {to}")
            return True

        except Exception as e:
            logger.error(f"Gmail send failed: {str(e)}")
            return False

    @staticmethod
    def _send_via_sendmail(
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        from_email: str,
        from_name: str,
    ) -> bool:
        """Send email via local sendmail command."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = to

            # Attach parts
            part1 = MIMEText(body_text, "plain")
            part2 = MIMEText(body_html, "html")
            msg.attach(part1)
            msg.attach(part2)

            # Use sendmail command
            process = subprocess.Popen(
                ["/usr/sbin/sendmail", "-t", "-oi"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = process.communicate(msg.as_bytes())

            if process.returncode != 0:
                logger.error(f"Sendmail failed: {stderr.decode()}")
                return False

            logger.info(f"Email sent via sendmail to {to}")
            return True

        except Exception as e:
            logger.error(f"Sendmail send failed: {str(e)}")
            return False

    @staticmethod
    def send_verification_email(email: str, token: str, user_name: str) -> bool:
        """
        Send email verification email to user.

        Args:
            email: User's email address
            token: Verification token
            user_name: User's name

        Returns:
            True if email sent successfully, False otherwise
        """
        # Import here to avoid circular dependency
        from app.services.system_settings_service import SystemSettingsService

        try:
            site_url = SystemSettingsService.get_setting("site_url", Config.SITE_URL)
            site_name = SystemSettingsService.get_setting("site_name", Config.APP_NAME)

            verification_url = f"{site_url}/verify-email/{token}"

            subject = f"Verify your {site_name} email address"

            body_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{site_name}</h1>
                    </div>
                    <div class="content">
                        <h2>Welcome, {user_name}!</h2>
                        <p>Thank you for signing up for {site_name}. Please verify your email address to complete your registration.</p>
                        <p>Click the button below to verify your email:</p>
                        <p style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Email Address</a>
                        </p>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #4F46E5;">{verification_url}</p>
                        <p><strong>This link will expire in 24 hours.</strong></p>
                        <p>If you didn't create an account with {site_name}, you can safely ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; {site_name}. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            body_text = f"""
            Welcome, {user_name}!

            Thank you for signing up for {site_name}. Please verify your email address to complete your registration.

            Click or copy this link to verify your email:
            {verification_url}

            This link will expire in 24 hours.

            If you didn't create an account with {site_name}, you can safely ignore this email.

            ---
            {site_name}
            """

            return EmailService.send_email(
                to=email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
            )

        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return False
