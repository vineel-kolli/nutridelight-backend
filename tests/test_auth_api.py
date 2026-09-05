
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.dependencies import ADMIN_SESSION_COOKIE
from app.core.database import SessionLocal
from app.main import app
from app.models.admin_session import AdminSession
from app.models.admin_user import AdminUser
from app.services.auth_service import hash_password


client = TestClient(app)


def create_test_admin(
    username: str = "testadmin",
    password: str = "TestPassword123!",
) -> AdminUser:
    db = SessionLocal()

    try:
        admin = AdminUser(
            username=username,
            password_hash=hash_password(password),
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        return admin

    finally:
        db.close()


def cleanup_auth_data() -> None:
    db = SessionLocal()

    try:
        db.query(AdminSession).delete()
        db.query(AdminUser).delete()
        db.commit()

    finally:
        db.close()


def setup_function() -> None:
    cleanup_auth_data()


def teardown_function() -> None:
    cleanup_auth_data()


def test_login_with_valid_credentials_returns_cookie():
    create_test_admin()

    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "testadmin",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["admin"]["username"] == "testadmin"
    assert "password_hash" not in body

    assert ADMIN_SESSION_COOKIE in response.cookies


def test_login_with_invalid_password_returns_401():
    create_test_admin()

    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "testadmin",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_login_with_unknown_username_returns_401():
    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "doesnotexist",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_me_requires_authentication():
    response = client.get("/api/v1/admin/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_me_returns_authenticated_admin():
    create_test_admin()

    login_response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "testadmin",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    response = client.get("/api/v1/admin/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == "testadmin"


def test_logout_revokes_session():
    create_test_admin()

    login_response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "testadmin",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    session_token = login_response.cookies.get(
        ADMIN_SESSION_COOKIE
    )

    assert session_token is not None

    logout_response = client.post(
        "/api/v1/admin/auth/logout"
    )

    assert logout_response.status_code == 200

    me_response = client.get(
        "/api/v1/admin/auth/me"
    )

    assert me_response.status_code == 401

    db = SessionLocal()

    try:
        token_hashes = db.execute(
            select(AdminSession.token_hash)
        ).scalars().all()

        # There should be no active session.
        active_sessions = db.execute(
            select(AdminSession).where(
                AdminSession.revoked_at.is_(None)
            )
        ).scalars().all()

        assert len(active_sessions) == 0

    finally:
        db.close()


def test_inactive_admin_cannot_login():
    db = SessionLocal()

    try:
        admin = AdminUser(
            username="inactiveadmin",
            password_hash=hash_password(
                "TestPassword123!"
            ),
            is_active=False,
        )

        db.add(admin)
        db.commit()

    finally:
        db.close()

    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "inactiveadmin",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 401


def test_invalid_session_cookie_returns_401():
    client.cookies.set(
        ADMIN_SESSION_COOKIE,
        "invalid-session-token",
    )

    response = client.get(
        "/api/v1/admin/auth/me"
    )

    assert response.status_code == 401

    client.cookies.clear()