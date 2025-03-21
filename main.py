from fasthtml.common import *
from dataclasses import dataclass
import secrets
import os
import dotenv
import schedule
import threading
import time
import secrets
from subscribe import send_verification_email
from mailer import send_email

app, rt = fast_app()
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
            print(f"Scheduled job for {job.job_func.args}")
        print("\n")

@rt("/")
def get():
    return Titled("User Registration",
                  Form(Input(type="text", name="username", placeholder="Username"),
                       Input(type="email", name="email", placeholder="Email"),
                       Input(type="time", name="email_time", placeholder="Select Time"),
                       Button("Register", type="submit"),
                       hx_post="/register",
                       hx_target="#result"
                       ),
                       Div(id="result")
                       )

@rt("/register")
def post(username: str, email: str, email_time: str):
    token = secrets.token_urlsafe(16)
    user = TempUser(username=username, email=email, email_time=email_time, token=token)
    print(user)
    errors = validate_user(user)
    if errors:
        return Div(Ul(*[Li(error) for error in errors]), id="result", style="color: red;")

    sender_email = "daybreakdigests@gmail.com" 
    sender_password = os.getenv("GMAIL_PASS")

    email_sent = send_verification_email(sender_email, sender_password, user.email, token)

    if email_sent:
        existing_user = db.q("SELECT * FROM temp_users WHERE email=?", (user.email,))
        if existing_user:
            return Div(f"Email {user.email} is already registered.", id="result", style="color: red;")
        
        db.t.temp_users.insert(user)
        return Div(f"Verification email sent to {user.email}. Please check your inbox.", id="result", style="color: blue;")
    else:
        return Div("Could not send verification email. Please try again.", id="result", style="color: red;")


@rt("/verify")
def verify(token: str):
    user = db.q("SELECT * FROM temp_users WHERE token=?", (token,))
    print(user)
    print(token)
    all_tmp = db.q("SELECT * FROM temp_users")
    print(all_tmp)
    if user:
        db.t.users.insert(username=user[0]["username"], email=user[0]["email"], email_time=user[0]["email_time"])
        db.q("DELETE FROM temp_users WHERE token=?", (token,))

        return Div(f"Email verified! Welcome, {user[0]['username']}.", style="color: green;")
    else:
        return Div("Invalid or expired token.", style="color: red;")

def on_server_start():
    load_existing_schedules()
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

if __name__ == "__main__":
    on_server_start()
    print("start")

    serve(host="192.168.0.108", port=5001)