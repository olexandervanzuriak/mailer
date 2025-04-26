import pytest
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from main import app

# Test home page response
@pytest.mark.asyncio
async def test_home_page():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
        
        assert response.status_code == 200
        assert "DayBreak Digests" in response.text

# Test registration page response
@pytest.mark.asyncio
async def test_register_get():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/register")
        
        assert response.status_code == 200
        assert "Registration" in response.text

# Test news history page response
@pytest.mark.asyncio
async def test_news_history_get():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/news_history")
        
        assert response.status_code == 200
        assert "Select a date and news source" in response.text
