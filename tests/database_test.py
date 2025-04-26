import pytest
from fasthtml.common import database
from main import app, validate_user, TempUser

TEST_DB_PATH = "data/test_example.db"

# Fixture to create a clean test database
@pytest.fixture
def test_db():
    db = database(TEST_DB_PATH)
    
    db.q("DROP TABLE IF EXISTS users")
    db.q("DROP TABLE IF EXISTS temp_users")
    db.q("DROP TABLE IF EXISTS news_archive")
    
    db.t.users.create(id=int, username=str, email=str, email_time=str, news_channel=str, pk='id')
    db.t.temp_users.create(username=str, email=str, email_time=str, news_channel=str, token=str, pk='email')
    db.t.news_archive.create(id=int, date=str, news_channel=str, title=str, description=str, link=str, time=str, pk="id")
    
    return db

# Test user validation function
def test_user_validation():
    user = TempUser(username="Jo", email="not_an_email", email_time="", news_channel="tsn", token="123")
    errors = validate_user(user)
    
    assert "Username must be at least 3 characters long" in errors
    assert "Invalid email address" in errors
    assert "Email time must be selected" in errors

    valid_user = TempUser(username="John", email="john@example.com", email_time="12:00", news_channel="tsn", token="abc")
    
    assert validate_user(valid_user) == []

# Test inserting and querying a user
def test_insert_and_query_user(test_db):
    test_db.t.users.insert(id=1, username="Jane", email="jane@example.com", email_time="10:00", news_channel="epravda")
    
    result = test_db.q("SELECT * FROM users WHERE email=?", ("jane@example.com",))
    
    assert result[0]["username"] == "Jane"

# Test for uniqueness constraint on temp_users table
def test_temp_user_uniqueness(test_db):
    user = {
        "username": "TestUser",
        "email": "test@example.com",
        "email_time": "09:00",
        "news_channel": "tsn",
        "token": "tok123"
    }
    
    test_db.t.temp_users.insert(user)
    
    with pytest.raises(Exception):
        test_db.t.temp_users.insert(user)
