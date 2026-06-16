import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import random
import string
import argparse

# Load environment variables
load_dotenv()

# Email configuration
SMTP_SERVER = os.getenv("EMAIL_HOST")
SMTP_PORT = int(os.getenv("EMAIL_PORT", "2525"))
SMTP_USERNAME = os.getenv("EMAIL_USER")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Use the authenticated username as sender (this is what Elastic Email allows)
SENDER_EMAIL = SMTP_USERNAME

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_email(to_email, subject, body):
    """
    Send an email using SMTP configuration
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (HTML)
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD]):
        print("Email configuration is incomplete")
        return False
    
    try:
        # Create message
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        
        # Add body to email
        message.attach(MIMEText(body, "html"))
        
        # Convert the message to a string
        msg = message.as_string()
        
        # Connect to SMTP server and send email
        print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp.set_debuglevel(1)  # Enable verbose logging
        smtp.ehlo()
        smtp.starttls()
        
        print(f"Logging in as {SMTP_USERNAME}...")
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        print(f"Sending email from {SENDER_EMAIL} to {to_email}...")
        smtp.sendmail(SENDER_EMAIL, to_email, msg)
        smtp.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def send_verification_email(to_email, otp):
    """
    Send a verification email with OTP
    
    Args:
        to_email: Recipient email address
        otp: One-time password for verification
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = "Verify Your Email Address"
    body = f"""
    <html>
    <body>
        <h2>Email Verification</h2>
        <p>Thank you for signing up! Please use the following verification code to complete your registration:</p>
        <h1 style="font-size: 24px; background-color: #f0f0f0; padding: 10px; text-align: center;">{otp}</h1>
        <p>This code will expire in 10 minutes.</p>
        <p>If you didn't request this verification, please ignore this email.</p>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, body)

def send_password_reset_email(to_email, otp):
    """
    Send a password reset email with OTP
    
    Args:
        to_email: Recipient email address
        otp: One-time password for password reset
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = "Reset Your Password"
    body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>We received a request to reset your password. Please use the following verification code to reset your password:</p>
        <h1 style="font-size: 24px; background-color: #f0f0f0; padding: 10px; text-align: center;">{otp}</h1>
        <p>This code will expire in 10 minutes.</p>
        <p><strong>If you didn't request this password reset, please ignore this email and your password will remain unchanged.</strong></p>
        <p>For security reasons, this code can only be used once.</p>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, body)

def send_mentor_invite_email(to_email, invite_link):
    """
    Send a mentor invitation email containing the tokenized accept link.

    Args:
        to_email: Recipient email address
        invite_link: The tokenized link the mentor clicks to accept

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = "You're invited to join CDEN as a mentor"
    body = f"""
    <html>
    <body>
        <h2>Mentor Invitation</h2>
        <p>You have been invited to join CDEN, Canada's community for disabled entrepreneurs, as a mentor.</p>
        <p>Click the link below to accept your invitation and set up your account:</p>
        <p><a href="{invite_link}">{invite_link}</a></p>
        <p>This invitation will expire in 7 days.</p>
        <p>If you weren't expecting this invitation, you can safely ignore this email.</p>
    </body>
    </html>
    """

    return send_email(to_email, subject, body)


def send_mentor_request_email(to_email, founder_label):
    """Notify a mentor that a founder has requested to connect.

    Args:
        to_email: The mentor's email address
        founder_label: A name to show for the founder (business or full name)
    """
    subject = "A founder has requested you as a mentor on CDEN"
    body = f"""
    <html>
    <body>
        <h2>New Mentor Request</h2>
        <p><strong>{founder_label}</strong> has requested to connect with you as a mentor on CDEN.</p>
        <p>Log in to your dashboard to review the request and accept or decline it.</p>
    </body>
    </html>
    """
    return send_email(to_email, subject, body)


def send_match_confirmed_email(to_email, mentor_label):
    """Notify a founder that a mentor has accepted their request.

    Args:
        to_email: The founder's email address
        mentor_label: A name to show for the mentor
    """
    subject = "Your mentor request was accepted on CDEN"
    body = f"""
    <html>
    <body>
        <h2>You're Connected!</h2>
        <p><strong>{mentor_label}</strong> has accepted your request and is now your mentor on CDEN.</p>
        <p>Log in to your dashboard to see the connection and reach out.</p>
    </body>
    </html>
    """
    return send_email(to_email, subject, body)


def main():
    """CLI interface for testing email functionality"""
    parser = argparse.ArgumentParser(description='Send test emails via command line')
    parser.add_argument('--to', required=True, help='Recipient email address')
    parser.add_argument('--subject', default='Test Email', help='Email subject')
    parser.add_argument('--body', default='This is a test email sent from the CLI.', help='Email body')
    parser.add_argument('--verify', action='store_true', help='Send a verification email with OTP instead')
    
    args = parser.parse_args()
    
    if args.verify:
        otp = generate_otp()
        print(f"Generated OTP: {otp}")
        success = send_verification_email(args.to, otp)
    else:
        success = send_email(args.to, args.subject, args.body)
    
    if success:
        print("Email sent successfully!")
    else:
        print("Failed to send email.")

if __name__ == "__main__":
    main() 