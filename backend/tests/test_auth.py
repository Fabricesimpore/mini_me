import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def test_user():
    return {
        "email": "testuser@example.com",
        "name": "Test User",
        "password": "TestPassword123"
    }

def test_register(test_user):
    response = client.post("/register", json=test_user)
    data = response.json()
    assert ("email" in data and data["email"] == test_user["email"]) or ("error" in data and "already exists" in data["error"])

def test_register_duplicate(test_user):
    # Register once
    client.post("/register", json=test_user)
    # Register again with same email
    response = client.post("/register", json=test_user)
    assert response.status_code == 200 or response.status_code == 400
    data = response.json()
    assert "email" in data or "error" in data


def test_login(test_user):
    response = client.post("/login", data={
        "username": test_user["email"],
        "password": test_user["password"],
        "grant_type": "password"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    global access_token
    access_token = data["access_token"]


def test_login_wrong_password(test_user):
    response = client.post("/login", data={
        "username": test_user["email"],
        "password": "WrongPassword"
    })
    assert response.status_code == 200
    assert response.json().get("error") == "Incorrect email or password"


def test_me_protected(test_user):
    # Login to get token
    response = client.post("/login", data={
        "username": test_user["email"],
        "password": test_user["password"],
        "grant_type": "password"
    })
    token = response.json()["access_token"]
    # Access /me
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]


def test_me_protected_no_token():
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_update_me(test_user):
    # Login to get token
    response = client.post("/login", data={
        "username": test_user["email"],
        "password": test_user["password"],
        "grant_type": "password"
    })
    token = response.json()["access_token"]
    # Update name
    new_name = "Updated User"
    response = client.put("/me", json={"name": new_name}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_name 


def test_update_me_invalid_email(test_user):
    # Login to get token
    login = client.post("/login", data={
        "username": test_user["email"],
        "password": test_user["password"]
    })
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    # Try to update with invalid email
    response = client.put("/me", json={"email": "not-an-email"}, headers=headers)
    assert response.status_code == 422


def test_me_invalid_jwt():
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = client.get("/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials" 