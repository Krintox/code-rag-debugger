# File: services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send an email"""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning("SMTP configuration missing, email not sent")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email to new user"""
        subject = "Welcome to RodeCeview!"
        html_content = f"""
        <html>
        <body>
            <h1>Welcome to RodeCeview, {username}!</h1>
            <p>Thank you for joining our code evolution tracking platform.</p>
            <p>Start by adding your first project and exploring the features.</p>
            <br>
            <p>Best regards,<br>The RodeCeview Team</p>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, html_content)

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        subject = "Password Reset Request"
        reset_url = f"https://rodeceview.vercel.app/reset-password?token={reset_token}"
        html_content = f"""
        <html>
        <body>
            <h1>Password Reset Request</h1>
            <p>You requested to reset your password. Click the link below to proceed:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <br>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, html_content)

    def send_project_notification(self, to_email: str, project_name: str, message: str) -> bool:
        """Send project notification email"""
        subject = f"Project Update: {project_name}"
        html_content = f"""
        <html>
        <body>
            <h1>Project Update: {project_name}</h1>
            <p>{message}</p>
            <br>
            <p>View your project: <a href="https://rodeceview.vercel.app/projects">RodeCeview Dashboard</a></p>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, html_content)

email_service = EmailService()