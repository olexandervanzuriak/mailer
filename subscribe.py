import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BASE_URL = "http://192.168.0.105:5001/"

def send_verification_email(sender_email, sender_password, recipient_email, token):
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)

            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = recipient_email
            message["Subject"] = "Confirm Your Email"

            verification_link = f"{BASE_URL}verify?token={token}"
            body = f"""
            Hello,  
            Click the link below to confirm your email:  
            {verification_link}  
            
            If you didn't request this, please ignore this email.  
            """
            message.attach(MIMEText(body, "plain"))

            server.send_message(message)
            print(f"Verification email sent to {recipient_email}")
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
