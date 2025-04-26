import os
import ssl
import base64
import dotenv
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

dotenv.load_dotenv("config.env")

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465
BASE_URL = os.getenv("BASE_URL")

def send_verification_email(sender_email, sender_password, recipient_email, token):
    """Send a verification email with a confirmation link."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((SMTP_SERVER, SMTP_PORT)) as sock:
            with context.wrap_socket(sock, server_hostname=SMTP_SERVER) as server:
                server.recv(1024)  # Receive initial server response

                # Send EHLO command
                server.sendall(b"EHLO localhost\r\n")
                server.recv(1024)  # Receive server response

                # Authentication message (Base64 encoded)
                auth_msg = f"\0{sender_email}\0{sender_password}"
                auth_encoded = base64.b64encode(auth_msg.encode()).decode()
                server.sendall(f"AUTH PLAIN {auth_encoded}\r\n".encode())
                server.recv(1024)  # Server response

                # Send email details
                server.sendall(f"MAIL FROM:<{sender_email}>\r\n".encode())
                server.recv(1024)
                server.sendall(f"RCPT TO:<{recipient_email}>\r\n".encode())
                server.recv(1024)
                server.sendall(b"DATA\r\n")
                server.recv(1024)

                # Create verification link and email body
                verification_link = f"{BASE_URL}verify?token={token}"
                body = f"""
                Hello,  
                Click the link below to confirm your email:  
                {verification_link}  
                
                If you didn't request this, please ignore this email.  
                """
                message = (
                    f"From: {sender_email}\r\n"
                    f"To: {recipient_email}\r\n"
                    "Subject: Confirm Your Email\r\n"
                    "Content-Type: text/plain; charset=UTF-8\r\n"
                    "\r\n"
                    f"{body}\r\n"
                    ".\r\n"
                )
                server.sendall(message.encode())
                server.recv(1024)

                # Send QUIT command
                server.sendall(b"QUIT\r\n")
                server.recv(1024)

                print(f"Verification email sent to {recipient_email}")
                return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
