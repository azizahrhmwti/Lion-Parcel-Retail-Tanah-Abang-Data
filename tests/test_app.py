from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database import SessionLocal
from app.main import app, seed_database
from app.models import Lead, LeadStatus


client = TestClient(app)


def test_login_page_loads():
    response = client.get("/login")
    assert response.status_code == 200
    assert "Selamat datang" in response.text


def test_admin_can_login_and_open_dashboard():
    response = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Total leads" in response.text


def test_anonymous_user_is_redirected():
    response = TestClient(app).get("/leads", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_seed_is_idempotent():
    seed_database()
    with SessionLocal() as db:
        first_count = db.scalar(select(func.count(Lead.id)))
    seed_database()
    with SessionLocal() as db:
        second_count = db.scalar(select(func.count(Lead.id)))
    assert first_count == second_count


def test_seed_contains_routed_visits():
    seed_database()
    with SessionLocal() as db:
        routed = db.scalar(select(func.count(Lead.id)).where(Lead.status == LeadStatus.ROUTED.value))
        assert routed == 36
