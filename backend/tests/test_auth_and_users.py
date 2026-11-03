import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import get_password_hash, verify_password

client = TestClient(app)

def test_password_hashing():
    pwd = "SecretPassword123!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_user_registration_and_login():
    email = "surveyor_test@jatayuv.ai"
    password = "SecurePassword2026!"
    
    # 1. Register
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Senior Field Surveyor",
            "role": "analyst",
        },
    )
    assert reg_resp.status_code in [201, 400]  # 400 if already created in previous run
    
    # 2. Login JSON
    login_resp = client.post(
        "/api/v1/auth/login/json",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 3. Access Profile /me
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    user_info = me_resp.json()
    assert user_info["email"] == email
    assert user_info["full_name"] == "Senior Field Surveyor"

def test_duplicate_registration_fails():
    email = "duplicate_test@jatayuv.ai"
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "Test Duplicate",
        "role": "analyst",
    }
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code in [201, 400]
    
    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already exists" in r2.json()["detail"]

