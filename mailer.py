import socket
import ssl
import base64
import os
import feedparser
import dotenv
from datetime import datetime

dotenv.load_dotenv("conf.env")

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465
SENDER_EMAIL = 'daybreakdigests@gmail.com'
SENDER_APP_PASSWORD = os.getenv("GMAIL_PASS")


def format_date(date_string):
    """Convert full datetime to 'DD Month, HH:MM' format"""
    try:
        parsed_date = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
        return parsed_date.strftime("%d %B, %H:%M")  # Example: '23 March, 20:49'
    except ValueError:
        return date_string  # If parsing fails, return the original string


def fetch_news():
    """Fetch latest news from RSS feed"""
    EMAIL_BODY = """
    <html>
    <body style="font-family: Arial, sans-serif;">
    <h2 style="text-align: center;">📰 Today's News</h2>
    """
    d = feedparser.parse('https://www.pravda.com.ua/rss/view_mainnews/')
    for entry in d.entries[:5]:
        formatted_date = format_date(entry.published)
        EMAIL_BODY += (
            f"<h3 style='text-align: left;'><b>{entry.title}</b></h3>"
            f"<p style='text-align: left;'>{entry.description}</p>"
            f"<p style='text-align: left;'><strong>Published:</strong> {formatted_date}</p>"
            f"<p style='text-align: left;'><a href='{entry.link}' style='text-decoration: none; color: #1a73e8;'>🔗 Read more</a></p>"
            "<hr style='width: 50%; margin-left: 0; border: 1px solid #ddd;'>"
        )
    EMAIL_BODY += """
    </body>
    </html>
    """
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
                "Content-Type: text/html; charset=UTF-8\r\n"
                "\r\n"
                f"{email_body}\r\n"
                ".\r\n"
            )
            server.sendall(email_message.encode())
            server.recv(1024)

            server.sendall(b"QUIT\r\n")
            server.recv(1024)

            print(f"Email sent to {recipient_email} successfully!")
