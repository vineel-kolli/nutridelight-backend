from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import ADMIN_SESSION_COOKIE
from app.main import app
from app.models.admin_session import AdminSession
from app.models.admin_user import AdminUser
from app.models.game_config import GameConfig
from app.models.prize_rule import PrizeRule
from app.services.auth_service import hash_password


client = TestClient(app)


TEST_USERNAME = "testadmin"
TEST_PASSWORD = "TestPassword123!"
FRONTEND_ORIGIN = "http://localhost:5173"


def create_test_admin(
    db: Session,
    username: str = TEST_USERNAME,
    password: str = TEST_PASSWORD,
) -> AdminUser:
    admin = AdminUser(
        username=username,
        password_hash=hash_password(password),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    return admin


def create_test_game_config(
    db: Session,
    total_games: int = 5,
) -> GameConfig:
    game_config = GameConfig(
        total_games=total_games,
        is_active=True,
    )

    db.add(game_config)
    db.flush()

    return game_config


def create_test_prize_rule(
    db: Session,
    game_config_id: int,
    required_wins: int = 5,
) -> PrizeRule:
    prize_rule = PrizeRule(
        game_config_id=game_config_id,
        required_wins=required_wins,
        prize_name="30% Discount",
        prize_image_url="https://example.com/prize.png",
        is_active=True,
    )

    db.add(prize_rule)
    db.flush()

    return prize_rule


def login_test_admin() -> None:
    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200


def test_login_with_valid_credentials_returns_cookie(db):
    create_test_admin(db)

    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["admin"]["username"] == TEST_USERNAME
    assert "password_hash" not in body

    assert ADMIN_SESSION_COOKIE in response.cookies


def test_login_with_invalid_password(db):
    create_test_admin(db)

    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_login_with_unknown_username():
    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "doesnotexist",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_me_requires_authentication():
    client.cookies.clear()

    response = client.get(
        "/api/v1/admin/auth/me"
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_me_returns_authenticated_admin(db):
    client.cookies.clear()

    create_test_admin(db)

    login_response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    response = client.get(
        "/api/v1/admin/auth/me"
    )

    assert response.status_code == 200
    assert response.json()["username"] == TEST_USERNAME


def test_logout_revokes_session(db):
    client.cookies.clear()

    create_test_admin(db)

    login_response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
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

    active_sessions = db.execute(
        select(AdminSession).where(
            AdminSession.revoked_at.is_(None)
        )
    ).scalars().all()

    assert len(active_sessions) == 0


def test_inactive_admin_cannot_login(db):
    client.cookies.clear()

    admin = AdminUser(
        username="inactiveadmin",
        password_hash=hash_password(TEST_PASSWORD),
        is_active=False,
    )

    db.add(admin)
    db.flush()

    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": "inactiveadmin",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 401


def test_invalid_session_cookie_returns_401():
    client.cookies.clear()

    client.cookies.set(
        ADMIN_SESSION_COOKIE,
        "invalid-session-token",
    )

    response = client.get(
        "/api/v1/admin/auth/me"
    )

    assert response.status_code == 401

    client.cookies.clear()


def test_expired_session_cookie_returns_401(db):
    client.cookies.clear()

    create_test_admin(db)

    login_response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    session_token = login_response.cookies.get(
        ADMIN_SESSION_COOKIE
    )

    assert session_token is not None

    session = db.execute(
        select(AdminSession).where(
            AdminSession.token_hash.is_not(None)
        )
    ).scalars().first()

    assert session is not None

    session.expires_at = (
        datetime.now(UTC) - timedelta(minutes=1)
    )

    db.flush()

    client.cookies.set(
        ADMIN_SESSION_COOKIE,
        session_token,
    )

    response = client.get(
        "/api/v1/admin/auth/me"
    )

    assert response.status_code == 401

    client.cookies.clear()


def test_update_game_config_requires_authentication():
    client.cookies.clear()

    response = client.put(
        "/api/v1/game-config",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        json={
            "total_games": 5,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_update_game_config_allows_authenticated_admin(db):
    client.cookies.clear()

    create_test_admin(db)

    login_test_admin()

    response = client.put(
        "/api/v1/game-config",
        headers={
            "Origin": FRONTEND_ORIGIN,
        },
        json={
            "total_games": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["total_games"] == 5


def test_create_prize_rule_requires_authentication(db):
    client.cookies.clear()

    game_config = create_test_game_config(db)

    response = client.post(
        f"/api/v1/game-config/{game_config.id}/prize-rules",
        headers={
            "Origin": FRONTEND_ORIGIN,
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


def test_create_prize_rule_allows_authenticated_admin(db):
    client.cookies.clear()

    create_test_admin(db)

    game_config = create_test_game_config(db)

    login_test_admin()

    response = client.post(
        f"/api/v1/game-config/{game_config.id}/prize-rules",
        headers={
            "Origin": FRONTEND_ORIGIN,
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

    assert body["game_config_id"] == game_config.id
    assert body["required_wins"] == 5
    assert body["prize_name"] == "30% Discount"


def test_update_prize_rule_requires_authentication(db):
    client.cookies.clear()

    game_config = create_test_game_config(db)

    prize_rule = create_test_prize_rule(
        db,
        game_config.id,
    )

    response = client.put(
        f"/api/v1/game-config/{game_config.id}/prize-rules/{prize_rule.id}",
        headers={
            "Origin": FRONTEND_ORIGIN,
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


def test_update_prize_rule_allows_authenticated_admin(db):
    client.cookies.clear()

    create_test_admin(db)

    game_config = create_test_game_config(db)

    prize_rule = create_test_prize_rule(
        db,
        game_config.id,
    )

    login_test_admin()

    response = client.put(
        f"/api/v1/game-config/{game_config.id}/prize-rules/{prize_rule.id}",
        headers={
            "Origin": FRONTEND_ORIGIN,
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

    assert body["id"] == prize_rule.id
    assert body["game_config_id"] == game_config.id
    assert body["prize_name"] == "Updated Discount"


def test_public_game_config_does_not_require_admin_auth(db):
    client.cookies.clear()

    game_config = create_test_game_config(db)

    response = client.get(
        "/api/v1/game-config"
    )

    assert response.status_code == 200
    assert response.json()["total_games"] == game_config.total_games


def test_public_match_completion_does_not_require_admin_auth(db):
    client.cookies.clear()

    create_test_game_config(db)

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


def test_update_game_config_rejects_wrong_origin(db):
    client.cookies.clear()

    create_test_admin(db)

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


def test_update_game_config_rejects_missing_origin(db):
    client.cookies.clear()

    create_test_admin(db)

    login_test_admin()

    response = client.put(
        "/api/v1/game-config",
        json={
            "total_games": 5,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid request origin"


def test_create_prize_rule_rejects_wrong_origin(db):
    client.cookies.clear()

    create_test_admin(db)

    game_config = create_test_game_config(db)

    login_test_admin()

    response = client.post(
        f"/api/v1/game-config/{game_config.id}/prize-rules",
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


def test_update_prize_rule_rejects_wrong_origin(db):
    client.cookies.clear()

    create_test_admin(db)

    game_config = create_test_game_config(db)

    prize_rule = create_test_prize_rule(
        db,
        game_config.id,
    )

    login_test_admin()

    response = client.put(
        f"/api/v1/game-config/{game_config.id}/prize-rules/{prize_rule.id}",
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
    client.cookies.clear()

    response = client.get(
        "/api/v1/game-config/1/prize-rules"
    )

    assert response.status_code == 401