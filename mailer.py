from fasthtml.common import *
import socket
import ssl
import base64
import os
import feedparser
import dotenv
from datetime import datetime

db = database('data/example.db')
dotenv.load_dotenv("conf.env")

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465
SENDER_EMAIL = 'daybreakdigests@gmail.com'
SENDER_APP_PASSWORD = os.getenv("GMAIL_PASS")


def format_date(date_string):
    """Convert full datetime to 'DD Month, HH:MM' format in Ukrainian."""
    month_names = {
        "January": "січня", "February": "лютого", "March": "березня", "April": "квітня",
        "May": "травня", "June": "червня", "July": "липня", "August": "серпня",
        "September": "вересня", "October": "жовтня", "November": "листопада", "December": "грудня"
    }

    try:
        try:
            parsed_date = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            try:
                parsed_date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            except ValueError:
                return date_string

        month_english = parsed_date.strftime("%B")
        month_ukrainian = month_names.get(month_english, month_english)
        
        return parsed_date.strftime(f"%-d {month_ukrainian}, %H:%M")
    
    except Exception as e:
        print(f"Error formatting date: {e}")
        return date_string


def fetch_news_to_database(news_channel, save_to_db=True):
    """Fetch latest news from a specified channel and save to database if required."""
    
    feed_urls = {
        'ukrpravda': 'https://www.pravda.com.ua/rss/view_news/',
        'epravda': 'https://epravda.com.ua/rss/news/',
        'radiosvoboda': 'https://www.radiosvoboda.org/api/zrqitl-vomx-tpeoumq',
        'tsn': 'https://tsn.ua/rss/full.rss'
    }

    feed_url = feed_urls.get(news_channel)
    if not feed_url:
        return "Invalid news channel"

    d = feedparser.parse(feed_url)
    today_date = datetime.now().strftime("%Y-%m-%d")

    for entry in d.entries[:5]:
        formatted_date = format_date(entry.published)
        db.t.news_archive.insert(
            date=today_date,
            news_channel=news_channel,
            title=entry.title,
            description=entry.description,
            link=entry.link,
            time=formatted_date
        )


def fetch_news(news_channel):
    """Fetch latest news from the specified news channel and type."""
    EMAIL_BODY = """
    <html>
    <head>
        <style>
            body { 
                font-family: 'Times New Roman', serif; 
                background-color: #f2e6d9; /* Aged paper color */
                padding: 20px;
            }
            .container {
                max-width: 800px;
                background: #fffaf0;
                margin: auto;
                padding: 30px;
                box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
                border-radius: 8px;
                border: 1px solid #ccc;
            }
            h2 { 
                text-align: center; 
                font-size: 28px; 
                color: #222;
                font-family: 'Georgia', serif;
                border-bottom: 3px solid #444;
                padding-bottom: 10px;
            }
            h3 { 
                text-align: left; 
                font-size: 22px; 
                color: #111;
                font-weight: bold;
            }
            p { 
                text-align: justify; 
                font-size: 18px; 
                color: #333;
                line-height: 1.6;
            }
            .news-description { 
                font-size: 18px; 
                font-style: italic;
                color: #222; 
            }
            .news-link { 
                text-decoration: none; 
                color: #b22222; 
                font-weight: bold; 
                font-size: 16px; 
            }
            hr { 
                width: 100%; 
                border: 1px dashed #777; 
                margin: 20px 0; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📰 Сьогоднішні новини</h2>
    """
    
    if news_channel == 'ukrpravda':
        feed_url = 'https://www.pravda.com.ua/rss/view_news/'
    elif news_channel == 'epravda':
        feed_url = "https://epravda.com.ua/rss/news/"
    elif news_channel == 'radiosvoboda':
        feed_url = 'https://www.radiosvoboda.org/api/zrqitl-vomx-tpeoumq'
    elif news_channel == "tsn":
        feed_url = "https://tsn.ua/rss/full.rss"

    d = feedparser.parse(feed_url)
    
    for entry in d.entries[:5]:
        formatted_date = format_date(entry.published)
        EMAIL_BODY += (  
            f"<h3>{entry.title}</h3>"  
            f"<p class='news-description'>{entry.description}</p>"  
            f"<p><strong>Дата публікації:</strong> {formatted_date}</p>"  
            f"<p><a href='{entry.link}' class='news-link'>🔗 Докладніше</a></p>"  
            "<hr>"  
        )

    EMAIL_BODY += """
        </div>
    </body>
    </html>
    """
    
    return EMAIL_BODY


def send_email(recipient_email, subject="Today's News"):
    """Send an email using SMTP."""
    user = db.q("SELECT * FROM users WHERE email=?", (recipient_email,))
    email_body = fetch_news(user[0]["news_channel"])

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
