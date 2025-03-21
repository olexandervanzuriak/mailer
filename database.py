from fasthtml.common import *

# creates the SQLite database in the data/example.db file
db = database('data/example.db')

# Execute the query

# db.t.users.drop()
# db.t.temp_users.drop()
# make a table called "users"
users = db.t.users
temp_users = db.t.temp_users
print(db.q("SELECT * FROM temp_users"))
user_token = "SdOq4AngHwX9x7eb7X1I6Q"
db.q("DELETE FROM temp_users WHERE token=?", (user_token,))

# user1 = db.q("SELECT * FROM temp_users WHERE token=?", (user_token,))
# result = db.q("SELECT * FROM temp_users WHERE email=?", (email1,))[0]

# print(result)

if temp_users not in db.t:
    temp_users.create(username=str, email=str, email_time=str, token=str, pk='email')

if users not in db.t:
    users.create(id=int, username=str, email=str, email_time=str, pk='id')

#result = db.t.temp_users.execute("SELECT * FROM temp_users WHERE email=?", "dan@doe.com")
#users.insert(User(username="John Doe", email="john@doe.com", email_time="2020:04:12 12:30:00"))
#users.insert(User(username="Jane Doe", email="jane@doe.com", email_time="2020:04:12 12:30:00"))
#temp_users.insert(User(username="Dan L", email="dan@doe.com", email_time="2020:04:12 12:30:00"))