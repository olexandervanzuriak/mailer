from fasthtml.common import *

db = database('data/example.db')

users = db.t.users
temp_users = db.t.temp_users
news_archive = db.t.news_archive

# Check if temp_users table exists, and create it if not
if temp_users not in db.t:
    temp_users.create(
        username=str,
        email=str,
        email_time=str,
        news_channel=str,
        token=str,
        pk='email'
    )

# Check if users table exists, and create it if not
if users not in db.t:
    users.create(
        id=int,
        username=str,
        email=str,
        email_time=str,
        news_channel=str,
        pk='id'
    )

# Check if news_archive table exists, and create it if not
if news_archive not in db.t:
    news_archive.create(
        id=int,
        date=str,
        news_channel=str,
        title=str,
        description=str,
        link=str,
        time=str,
        pk="id"
    )
