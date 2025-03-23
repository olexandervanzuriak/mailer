from fasthtml.common import *
from dataclasses import dataclass
import secrets
import os
import dotenv
import schedule
import threading
import time
from subscribe import send_verification_email
from mailer import send_email

css = Link(rel="stylesheet", href="/static/styles.css")

app, rt = fast_app(hdrs=(css,), pico=False)
db = database('data/example.db')
dotenv.load_dotenv("config.env")

@dataclass
class TempUser:
    username: str
    email: str
    email_time: str
    token: str

class User:
    username: str
    email: str
    email_time: str

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

def schedule_daily_email(username, email, email_time):
    """Schedule the email sending at the user's chosen time."""
    
    job_identifier = (username, email, email_time)
    
    # Log the time being scheduled for clarity
    print(f"Scheduling email for {username} at {email_time}")

    # Ensure that the email_time is in the correct format HH:MM (24-hour format)
    try:
        time.strptime(email_time, "%H:%M")  # This will raise an error if the format is wrong
    except ValueError:
        print(f"Invalid time format: {email_time}. It should be in HH:MM format.")
        return
    
    existing_jobs = [job for job in schedule.get_jobs() 
                     if job.job_func.args == (username, email)]
    
    if existing_jobs:
        print(f"Email for {email} at {email_time} is already scheduled.")
    else:
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

def run_scheduler():
    """ Function to run the scheduler in the background """
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

@rt("/register")
def post(username: str, email: str, email_time: str):
    token = secrets.token_urlsafe(16)
    user = TempUser(username=username, email=email, email_time=email_time, token=token)
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
        return Div(f"Verification email sent to {user.email}. Please check your inbox.", id="result", style="color: blue;")
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

        db.t.users.insert(username=username, email=email, email_time=email_time)
        db.q("DELETE FROM temp_users WHERE token=?", (token,))

        schedule_daily_email(username, email, email_time)

        return Div(
                H2("Verification Successful!", style="color: white;"),
                P(f"Congratulations, {user[0]['username']}! Your email has been verified successfully.", style="color: white;"),
                P("You will start receiving daily emails at your chosen time.", style="color: white;"),
                P("If you have any issues, feel free to contact support.", style="color: white;"),
                cls="container"
            ),
    else:
        return Div(
            H2("Verification Failed", style="color: white;"),
            P("The verification link is invalid or has expired.", style="color: white;"),
            P("Please try registering again.", style="color: white;"),
            cls="container"
        )

def on_server_start():
    load_existing_schedules()
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

HOST_IP = os.getenv("HOST_IP", "127.0.0.1")
PORT = int(os.getenv("PORT", 5001))

if __name__ == "__main__":
    on_server_start()
    print("start")

    serve(host=HOST_IP, port=PORT)