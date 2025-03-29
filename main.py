from fasthtml.common import *
from dataclasses import dataclass
import secrets
import os
import dotenv
import schedule
import threading
import time
from datetime import datetime
from subscribe import send_verification_email
from mailer import send_email
from mailer import fetch_news_to_database

css = Link(rel="stylesheet", href="/static/styles.css?v=1")

app, rt = fast_app(hdrs=(css,), pico=False)
db = database('data/example.db')
dotenv.load_dotenv("config.env")

scheduler_thread = None


@dataclass
class TempUser:
    username: str
    email: str
    email_time: str
    news_channel: str 
    token: str


class User:
    username: str
    email: str
    email_time: str
    news_channel: str 


def validate_user(user: TempUser):
    errors = []
    if len(user.username) < 3:
        errors.append("Username must be at least 3 characters long")
    if '@' not in user.email or '.' not in user.email:
        errors.append("Invalid email address")
    if not user.email_time:
        errors.append("Email time must be selected")
    return errors


def send_daily_email(username, email):
    """Send daily emails using mailer.py"""
    print(f"Sending daily email to {username}")
    send_email(email)

def fetch_and_store_all_news():
    """Fetch and store news from all sources once a day."""
    news_channels = ["ukrpravda", "epravda", "radiosvoboda", "tsn"]
    for channel in news_channels:
        print(f"Fetching news for {channel}...")
        fetch_news_to_database(channel)
    print(f"News fetched and stored at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")

def schedule_daily_news_fetch():
    """Schedule the daily news fetching task."""
    schedule.every().day.at("11:10").do(fetch_and_store_all_news)


def clear_previous_task(username, email):
    """Clear any previous scheduled tasks for the user."""
    jobs_to_remove = [job for job in schedule.get_jobs() if job.job_func.args == (username, email)]
    for job in jobs_to_remove:
        print(f"Removing previous job for {username} at {email}")
        schedule.cancel_job(job)


def schedule_daily_email(username, email, email_time):
    """Schedule the email sending at the user's chosen time."""
    
    clear_previous_task(username, email)

    print(f"Scheduling email for {username} at {email_time}")

    try:
        time.strptime(email_time, "%H:%M")
    except ValueError:
        print(f"Invalid time format: {email_time}. It should be in HH:MM format.")
        return

    schedule.every().day.at(email_time).do(send_daily_email, username, email)
    print(f"Scheduled daily email for {username} at {email_time}")


def load_existing_schedules():
    """ Load all verified users and schedule their emails on startup """
    users = db.q("SELECT username, email, email_time FROM users")
    for user in users:
        if not any(job.job_func.args == (user["username"], user["email"]) for job in schedule.get_jobs()):
            schedule_daily_email(user["username"], user["email"], user["email_time"])
        else:
            print(f"User {user['username']} already has a scheduled email.")
    print("Restored email schedules for existing users.")


def stop_scheduler_thread():
    """ Stop the currently running scheduler thread safely. """
    global scheduler_thread
    if scheduler_thread and scheduler_thread.is_alive():
        print("Stopping the current scheduler thread.")
        scheduler_thread.join() 
        print("Scheduler thread stopped.")


def clear_all_jobs():
    """ Clears all scheduled jobs to ensure no duplicates. """
    print("Clearing all scheduled jobs.")
    schedule.clear()


def restart_scheduler():
    """Stop the previous scheduler thread, clear jobs, and start a new scheduler thread."""
    stop_scheduler_thread()
    clear_all_jobs()

    global scheduler_thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("New scheduler thread started.")


def run_scheduler():
    """Function to run the scheduler in the background."""
    while True:
        schedule.run_pending()
        time.sleep(60)
        for job in schedule.get_jobs():
            print(f"Job for {job.job_func.args} scheduled at {job.next_run}")
        print("\n")


@rt("/")
def get():
    return Titled(
        Div(
            H2("Hello, it's Day News!"),
            P("Stay updated with our daily news. If you want to subscribe, click the link below to register and receive our daily updates via email."),
            A("Click here to subscribe", href="/register", cls="subscribe-link"),
            P("Want to see past news?"),
            A("Click here for past news", href="/news_history", cls="news-archive-link"),
            Div(
                H3("Contact Us"),
                P("For any queries, feel free to reach out to us at"),
                A("daybreakdigests@gmail.com", href="mailto:daybreakdigests@gmail.com", cls="contact-link"),
                cls="contact-us"
            ),
            cls="main-content"
        )
    )

@rt("/register", methods="get")
def get():
        return Titled(
        Div(
            H2('Registration'),
            Form(
                Div(
                    Input(type='text', name="username", placeholder='Enter your username', required=''),
                    cls='input-box'
                ),
                Div(
                    Input(type='email', name="email", placeholder='Enter your email', required=''),
                    cls='input-box'
                ),
                Div(
                    Select(
                        Option('Українська правда', value='ukrpravda'),
                        Option('Радіо Свобода', value='radiosvoboda'),
                        Option('Економічна правда', value='epravda'),
                        Option('ТСН', value='tsn'),
                        name='news_channel', required='',
                    ),
                    cls='input-box'
                ),
                Div(
                    Input(type="time", name="email_time", placeholder="Select Time", required=''),
                    cls='input-box'
                ),
                Div(
                    Input(type="submit"),
                    cls='input-box button'
                ),
                hx_post="/register",
                hx_target="#result"
            ),
            Div(id="result", style="font-size: 16px;"),
            cls='wrapper'
        )
    )

@rt("/register", methods="post")
def post(username: str, email: str, email_time: str, news_channel: str):
    token = secrets.token_urlsafe(16)
    user = TempUser(username=username, email=email, email_time=email_time, news_channel=news_channel, token=token)
    print(user)
    errors = validate_user(user)
    if errors:
        return Div(Ul(*[Li(error) for error in errors]), id="result", style="color: red;")

    existing_user = db.q("SELECT * FROM temp_users WHERE email=?", (user.email,))
    if existing_user:
        return Div(f"Email {user.email} is already registered.", id="result", style="color: red;")

    sender_email = "daybreakdigests@gmail.com" 
    sender_password = os.getenv("GMAIL_PASS")
        
    email_sent = send_verification_email(sender_email, sender_password, user.email, token)

    if email_sent:
        db.t.temp_users.insert(user)
        return Div(f"Verification email sent to {user.email}. Please check your inbox.", id="result", style="color: black;")
    else:
        return Div("Could not send verification email. Please try again.", id="result", style="color: red;")


@rt("/verify")
def verify(token: str):
    user = db.q("SELECT * FROM temp_users WHERE token=?", (token,))
    all_tmp = db.q("SELECT * FROM temp_users")

    if user:
        username = user[0]["username"]
        email = user[0]["email"]
        email_time = user[0]["email_time"]
        news_channel = user[0]["news_channel"]

        db.t.users.insert(username=username, email=email, email_time=email_time, news_channel=news_channel)
        db.q("DELETE FROM temp_users WHERE token=?", (token,))


        restart_scheduler()
        schedule_daily_email(username, email, email_time)

        return Div(
                H2("Verification Successful!", style="color: black;"),
                P(f"Congratulations, {user[0]['username']}! Your email has been verified successfully.", style="color: black;"),
                P("You will start receiving daily emails at your chosen time.", style="color: black;"),
                P("If you have any issues, feel free to contact support.", style="color: black;"),
                cls="container"
            ),
    else:
        return Div(
            H2("Verification Failed", style="color: black;"),
            P("The verification link is invalid or has expired.", style="color: black;"),
            P("Please try registering again.", style="color: black;"),
            cls="container"
        )

@rt("/news_history", methods="get")
def get_news_history():
    return Titled(
        Div(
            H2("Select a Date and News Source to View Past News"),
            Form(
                Div(
                    Input(type="date", name="news_date", required=""),
                    cls="input-box"
                ),
                Div(
                    Select(
                        Option("Всі джерела", value="all"),
                        Option("Українська правда", value="ukrpravda"),
                        Option("Радіо Свобода", value="radiosvoboda"),
                        Option("Економічна правда", value="epravda"),
                        Option("ТСН", value="tsn"),
                        name="news_channel",
                        required=""
                    ),
                    cls="input-box"
                ),
                Div(
                    Input(type="submit", value="Переглянути новини"),
                    cls="input-box button"
                ),
                hx_post="/news_history",
                hx_target="#news_results",
                hx_swap="innerHTML"
            ),
            Div(id="news_results", style="font-size: 16px;"),
            cls="wrapper"
        )
    )


@rt("/news_history", methods="post")
def post_news_history(news_date: str, news_channel: str):
    """Retrieve past news based on selected date and source"""

    query = "SELECT * FROM news_archive WHERE date=?"
    params = [news_date]

    if news_channel and news_channel != "all":
        query += " AND news_channel=?"
        params.append(news_channel)

    news_records = db.q(query, params)

    if not news_records:
        return Div(f"Новини за {news_date} з {news_channel} не знайдено.", style="color: red;")

    return Div(
        H2(f"Новини за {news_date} ({news_channel if news_channel != 'all' else 'Всі джерела'})"),
        *[
            Div(
                H3(record["title"]),
                P(record["description"]),
                P(A("Читати більше", href=record["link"], target="_blank")),
                Hr()
            ) for record in news_records
        ]
    )



def on_server_start():
    load_existing_schedules()
    global scheduler_thread
    schedule_daily_news_fetch()
    if scheduler_thread is None or not scheduler_thread.is_alive():
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    print("Scheduler started.")


HOST_IP = os.getenv("HOST_IP", "127.0.0.1")
PORT = int(os.getenv("PORT", 5001))

if __name__ == "__main__":
    on_server_start()
    print("start")

    serve(host=HOST_IP, port=PORT)