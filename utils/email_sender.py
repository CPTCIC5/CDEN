import os
import requests
from dotenv import load_dotenv
import random
import string
import argparse

# Load environment variables
load_dotenv()

# Email configuration.
# We send via Resend's HTTP API (port 443) instead of SMTP because hosts like
# Render block outbound SMTP ports (25/465/587). HTTP works everywhere.
RESEND_API_URL = "https://api.resend.com/emails"
# The Resend API key. We accept a dedicated RESEND_API_KEY but fall back to
# EMAIL_PASSWORD, which already holds the key from the SMTP config.
RESEND_API_KEY = os.getenv("RESEND_API_KEY") or os.getenv("EMAIL_PASSWORD")

# The From address. Must be on a domain verified in Resend
# (e.g. noreply@powerspeak.app). onboarding@resend.dev works for test sends.
SENDER_EMAIL = os.getenv("EMAIL_FROM")

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_email(to_email, subject, body):
    """
    Send an email via the Resend HTTP API.

    Uses HTTPS (port 443) rather than SMTP so it works on hosts that block
    outbound SMTP ports (e.g. Render).

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body (HTML)

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not all([RESEND_API_KEY, SENDER_EMAIL]):
        print("Email configuration is incomplete (need RESEND_API_KEY/EMAIL_PASSWORD and EMAIL_FROM)")
        return False

    try:
        print(f"Sending email from {SENDER_EMAIL} to {to_email} via Resend API...")
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": SENDER_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": body,
            },
            timeout=15,
        )

        if response.status_code in (200, 201):
            print(f"Email sent successfully to {to_email} (id: {response.json().get('id')})")
            return True

        print(f"Failed to send email: HTTP {response.status_code} - {response.text}")
        return False

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