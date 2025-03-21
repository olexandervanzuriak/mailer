import socket
import ssl
import base64
import os
import feedparser
import dotenv

dotenv.load_dotenv("conf.env")

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465
SENDER_EMAIL = 'daybreakdigests@gmail.com'
SENDER_APP_PASSWORD = os.getenv("GMAIL_PASS")

def fetch_news():
    """Fetch latest news from RSS feed"""
    EMAIL_BODY = 'Today’s news:\n\n'
    d = feedparser.parse('https://www.pravda.com.ua/rss/view_mainnews/')
    for entry in d.entries[:3]:
        EMAIL_BODY += (
            f"Title: {entry.title}\n"
            f"Description: {entry.description}\n"
            f"Published: {entry.published}\n"
            f"Link: {entry.link}\n\n"
        )
    return EMAIL_BODY

def send_email(recipient_email, subject="Today's News"):
    """Send an email using SMTP"""
    email_body = fetch_news()

    context = ssl.create_default_context()
    with socket.create_connection((SMTP_SERVER, SMTP_PORT)) as sock:
        with context.wrap_socket(sock, server_hostname=SMTP_SERVER) as server:
            server.recv(1024)

            server.sendall(b"EHLO localhost\r\n")
            server.recv(1024)

            auth_msg = f"\0{SENDER_EMAIL}\0{SENDER_APP_PASSWORD}"
            auth_encoded = base64.b64encode(auth_msg.encode()).decode()
            server.sendall(f"AUTH PLAIN {auth_encoded}\r\n".encode())
            server.recv(1024)

            server.sendall(f"MAIL FROM:<{SENDER_EMAIL}>\r\n".encode())
            server.recv(1024)

            server.sendall(f"RCPT TO:<{recipient_email}>\r\n".encode())
            server.recv(1024)

            server.sendall(b"DATA\r\n")
            server.recv(1024)

            email_message = (
                f"From: {SENDER_EMAIL}\r\n"
                f"To: {recipient_email}\r\n"
                f"Subject: {subject}\r\n"
                "\r\n"
                f"{email_body}\r\n"
                ".\r\n"
            )
            server.sendall(email_message.encode())
            server.recv(1024)

            server.sendall(b"QUIT\r\n")
            server.recv(1024)

            print(f"Email sent to {recipient_email} successfully!")
