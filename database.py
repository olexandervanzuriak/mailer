from fasthtml.common import *

# creates the SQLite database in the data/example.db file
db = database('data/example.db')

# Execute the query

#db.t.users.drop()
#db.t.temp_users.drop()
# make a table called "users"
users = db.t.users
temp_users = db.t.temp_users
#print(db.q("SELECT * FROM users"))
#user_token = "SdOq4AngHwX9x7eb7X1I6Q"
print(db.q("DELETE FROM users"))

# user1 = db.q("SELECT * FROM temp_users WHERE token=?", (user_token,))
# result = db.q("SELECT * FROM temp_users WHERE email=?", (email1,))[0]

# print(result)

if temp_users not in db.t:
    temp_users.create(username=str, email=str, email_time=str, news_channel=str, token=str, pk='email')

if users not in db.t:
    users.create(id=int, username=str, email=str, email_time=str, news_channel=str, pk='id')

#result = db.t.temp_users.execute("SELECT * FROM temp_users WHERE email=?", "dan@doe.com")
#users.insert(username="John", email="sashavanzuriak@gmail.com", email_time="17:56")
#users.insert(username="John olexnader", email="sashavanzuriak@gmail.com", email_time="17:58")
users.insert(username="Jane Doe", email="sashavanzuriak@gmail.com", email_time="12:01", news_channel="epravda")
#temp_users.insert(User(username="Dan L", email="dan@doe.com", email_time="2020:04:12 12:30:00"))