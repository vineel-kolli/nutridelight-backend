
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.dependencies import ADMIN_SESSION_COOKIE
from app.core.database import SessionLocal
from app.main import app
from app.models.admin_session import AdminSession
from app.models.admin_user import AdminUser
from app.models.game_config import GameConfig
from app.models.prize_rule import PrizeRule
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


def test_expired_session_cookie_returns_401():
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

    db = SessionLocal()

    try:
        session = db.execute(
            select(AdminSession).where(
                AdminSession.token_hash.is_not(None)
            )
        ).scalars().first()

        assert session is not None

        from datetime import UTC, datetime, timedelta

        session.expires_at = datetime.now(UTC) - timedelta(
            minutes=1
        )

        db.commit()

    finally:
        db.close()

    client.cookies.set(
        ADMIN_SESSION_COOKIE,
        session_token,
    )

    response = client.get(
        "/api/v1/admin/auth/me"
    )

    assert response.status_code == 401

    client.cookies.clear()

def login_test_admin() -> None:
    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "testadmin",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200


def test_update_game_config_requires_authentication():
    response = client.put(
    "/api/v1/game-config",
    headers={
        "Origin": "http://localhost:5173",
    },
    json={
        "total_games": 5,
    },
)

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_update_game_config_allows_authenticated_admin():
    create_test_admin()

    login_test_admin()

    response = client.put(
    "/api/v1/game-config",
    headers={
        "Origin": "http://localhost:5173",
    },
    json={
        "total_games": 5,
    },
)

    assert response.status_code == 200
    assert response.json()["total_games"] == 5


def test_create_prize_rule_requires_authentication():
    db = SessionLocal()

    try:
        game_config = GameConfig(
            total_games=5,
            is_active=True,
        )

        db.add(game_config)
        db.commit()
        db.refresh(game_config)

        game_config_id = game_config.id

    finally:
        db.close()

    response = client.post(
    f"/api/v1/game-config/{game_config_id}/prize-rules",
    headers={
        "Origin": "http://localhost:5173",
    },
    json={
            "required_wins": 5,
            "prize_name": "30% Discount",
            "prize_image_url": "https://example.com/prize.png",
            "is_active": True,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_create_prize_rule_allows_authenticated_admin():
    create_test_admin()

    db = SessionLocal()

    try:
        game_config = GameConfig(
            total_games=5,
            is_active=True,
        )

        db.add(game_config)
        db.commit()
        db.refresh(game_config)

        game_config_id = game_config.id

    finally:
        db.close()

    login_test_admin()

    response = client.post(
    f"/api/v1/game-config/{game_config_id}/prize-rules",
    headers={
        "Origin": "http://localhost:5173",
    },
    json={
            "required_wins": 5,
            "prize_name": "30% Discount",
            "prize_image_url": "https://example.com/prize.png",
            "is_active": True,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["game_config_id"] == game_config_id
    assert body["required_wins"] == 5
    assert body["prize_name"] == "30% Discount"


def test_update_prize_rule_requires_authentication():
    db = SessionLocal()

    try:
        game_config = GameConfig(
            total_games=5,
            is_active=True,
        )

        db.add(game_config)
        db.flush()

        prize_rule = PrizeRule(
            game_config_id=game_config.id,
            required_wins=5,
            prize_name="30% Discount",
            prize_image_url="https://example.com/prize.png",
            is_active=True,
        )

        db.add(prize_rule)
        db.commit()
        db.refresh(game_config)
        db.refresh(prize_rule)

        game_config_id = game_config.id
        prize_rule_id = prize_rule.id

    finally:
        db.close()

    response = client.put(
    f"/api/v1/game-config/{game_config_id}/prize-rules/{prize_rule_id}",
    headers={
        "Origin": "http://localhost:5173",
    },
    json={
            "required_wins": 5,
            "prize_name": "Updated Discount",
            "prize_image_url": "https://example.com/updated.png",
            "is_active": True,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_update_prize_rule_allows_authenticated_admin():
    create_test_admin()

    db = SessionLocal()

    try:
        game_config = GameConfig(
            total_games=5,
            is_active=True,
        )

        db.add(game_config)
        db.flush()

        prize_rule = PrizeRule(
            game_config_id=game_config.id,
            required_wins=5,
            prize_name="30% Discount",
            prize_image_url="https://example.com/prize.png",
            is_active=True,
        )

        db.add(prize_rule)
        db.commit()
        db.refresh(game_config)
        db.refresh(prize_rule)

        game_config_id = game_config.id
        prize_rule_id = prize_rule.id

    finally:
        db.close()

    login_test_admin()

    response = client.put(
    f"/api/v1/game-config/{game_config_id}/prize-rules/{prize_rule_id}",
    headers={
        "Origin": "http://localhost:5173",
    },
    json={
            "required_wins": 5,
            "prize_name": "Updated Discount",
            "prize_image_url": "https://example.com/updated.png",
            "is_active": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == prize_rule_id
    assert body["game_config_id"] == game_config_id
    assert body["prize_name"] == "Updated Discount"


def test_public_game_config_does_not_require_admin_auth():
    db = SessionLocal()

    try:
        game_config = GameConfig(
            total_games=5,
            is_active=True,
        )

        db.add(game_config)
        db.commit()

    finally:
        db.close()

    response = client.get(
        "/api/v1/game-config"
    )

    assert response.status_code == 200
    assert response.json()["total_games"] == 5


def test_public_match_completion_does_not_require_admin_auth():
    db = SessionLocal()

    try:
        game_config = GameConfig(
            total_games=5,
            is_active=True,
        )

        db.add(game_config)
        db.commit()

    finally:
        db.close()

    response = client.post(
        "/api/v1/match/complete",
        json={
            "player_wins": 3,
            "buddy_wins": 2,
        },
    )

    assert response.status_code == 200
    assert response.json()["player_wins"] == 3
    assert response.json()["buddy_wins"] == 2


def login_test_admin() -> None:
    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "testadmin",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200


def test_update_game_config_rejects_wrong_origin():
    create_test_admin()

    login_test_admin()

    response = client.put(
        "/api/v1/game-config",
        headers={
            "Origin": "http://evil.example",
        },
        json={
            "total_games": 5,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid request origin"

def test_update_game_config_rejects_missing_origin():
    create_test_admin()

    login_test_admin()

    response = client.put(
        "/api/v1/game-config",
        json={
            "total_games": 5,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid request origin"



def test_create_prize_rule_rejects_wrong_origin():
    create_test_admin()

    db = SessionLocal()

    try:
        game_config = GameConfig(
            total_games=5,
            is_active=True,
        )

        db.add(game_config)
        db.commit()
        db.refresh(game_config)

        game_config_id = game_config.id

    finally:
        db.close()

    login_test_admin()

    response = client.post(
        f"/api/v1/game-config/{game_config_id}/prize-rules",
        headers={
            "Origin": "http://evil.example",
        },
        json={
            "required_wins": 5,
            "prize_name": "30% Discount",
            "prize_image_url": "https://example.com/prize.png",
            "is_active": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid request origin"



def test_update_prize_rule_rejects_wrong_origin():
    create_test_admin()

    db = SessionLocal()

    try:
        game_config = GameConfig(
            total_games=5,
            is_active=True,
        )

        db.add(game_config)
        db.flush()

        prize_rule = PrizeRule(
            game_config_id=game_config.id,
            required_wins=5,
            prize_name="30% Discount",
            prize_image_url="https://example.com/prize.png",
            is_active=True,
        )

        db.add(prize_rule)
        db.commit()
        db.refresh(prize_rule)

        game_config_id = game_config.id
        prize_rule_id = prize_rule.id

    finally:
        db.close()

    login_test_admin()

    response = client.put(
        f"/api/v1/game-config/{game_config_id}/prize-rules/{prize_rule_id}",
        headers={
            "Origin": "http://evil.example",
        },
        json={
            "required_wins": 5,
            "prize_name": "Updated Discount",
            "prize_image_url": "https://example.com/updated.png",
            "is_active": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid request origin"


def test_get_prize_rules_requires_auth():
    response = client.get(
        "/api/v1/game-config/1/prize-rules"
    )

    assert response.status_code == 401