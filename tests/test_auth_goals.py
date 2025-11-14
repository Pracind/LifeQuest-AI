import uuid
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _make_unique_email() -> str:
    return f"testuser_{uuid.uuid4().hex[:8]}@example.com"


def test_signup_login_and_goal_flow():
    # 1) Signup
    email = _make_unique_email()
    password = "supersecret123"
    display_name = "Test Flow User"

    signup_resp = client.post(
        "/signup",
        json={
            "email": email,
            "password": password,
            "display_name": display_name,
        },
    )
    assert signup_resp.status_code == 201, signup_resp.text
    data = signup_resp.json()
    assert data["email"] == email
    assert data["display_name"] == display_name
    assert "id" in data

    # 2) Login
    login_resp = client.post(
        "/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200, login_resp.text
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    access_token = token_data["access_token"]
    auth_header = {"Authorization": f"Bearer {access_token}"}

    # 3) Create goal
    goal_resp = client.post(
        "/goals",
        headers=auth_header,
        json={
            "title": "Test Goal via API",
            "description": "Testing goal creation endpoint",
        },
    )
    assert goal_resp.status_code == 201, goal_resp.text
    goal = goal_resp.json()
    assert goal["title"] == "Test Goal via API"
    assert goal["description"] == "Testing goal creation endpoint"
    assert "id" in goal
    goal_id = goal["id"]

    # 4) List goals
    list_resp = client.get("/goals", headers=auth_header)
    assert list_resp.status_code == 200, list_resp.text
    goals = list_resp.json()
    assert isinstance(goals, list)
    assert any(g["id"] == goal_id for g in goals)

    # 5) Get single goal
    get_resp = client.get(f"/goals/{goal_id}", headers=auth_header)
    assert get_resp.status_code == 200, get_resp.text
    goal_detail = get_resp.json()
    assert goal_detail["id"] == goal_id
    assert goal_detail["title"] == "Test Goal via API"
    assert "steps" in goal_detail
    assert isinstance(goal_detail["steps"], list)


def test_goals_requires_auth():
    # GET /goals without token should be unauthorized
    resp = client.get("/goals")
    assert resp.status_code == 401
    assert resp.json()["detail"] in ("Not authenticated", "Could not validate credentials")
