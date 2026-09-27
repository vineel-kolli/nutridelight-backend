import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.game_config import GameConfig
from app.models.prize_rule import PrizeRule

from app.models.admin_user import AdminUser
from app.services.auth_service import hash_password
from app.api.dependencies import ADMIN_SESSION_COOKIE




client = TestClient(app)


TEST_USERNAME = "testadmin"
TEST_PASSWORD = "TestPassword123!"


def create_test_admin(db: Session) -> AdminUser:
    admin = AdminUser(
        username=TEST_USERNAME,
        password_hash=hash_password(TEST_PASSWORD),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    return admin

def create_test_data(db: Session) -> GameConfig:
    game_config = GameConfig(
        total_games=5,
        is_active=True,
    )

    db.add(game_config)
    db.flush()

    db.add_all(
        [
            PrizeRule(
                game_config_id=game_config.id,
                required_wins=5,
                prize_name="30% Discount",
                prize_image_url="/30-percent.png",
                is_active=True,
            ),
            PrizeRule(
                game_config_id=game_config.id,
                required_wins=4,
                prize_name="32% Discount",
                prize_image_url="/32-percent.png",
                is_active=True,
            ),
            PrizeRule(
                game_config_id=game_config.id,
                required_wins=3,
                prize_name="Free Juice",
                prize_image_url="/free-juice.png",
                is_active=True,
            ),
        ]
    )

    db.flush()

    return game_config


@pytest.fixture(autouse=True)
def setup_match_data(db):
    client.cookies.clear()
    create_test_data(db)


def test_complete_match_four_player_wins():
    response = client.post(
        "/api/v1/match/complete",
        json={
            "player_wins": 4,
            "buddy_wins": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_games"] == 5
    assert data["player_wins"] == 4
    assert data["buddy_wins"] == 1
    assert data["winner"] == "player"
    assert data["reward_eligible"] is True
    assert data["prize_name"] == "32% Discount"


def test_complete_match_three_player_wins():
    response = client.post(
        "/api/v1/match/complete",
        json={
            "player_wins": 3,
            "buddy_wins": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["winner"] == "player"
    assert data["reward_eligible"] is True
    assert data["prize_name"] == "Free Juice"


def test_complete_match_two_player_wins():
    response = client.post(
        "/api/v1/match/complete",
        json={
            "player_wins": 2,
            "buddy_wins": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["winner"] == "buddy"
    assert data["reward_eligible"] is False
    assert data["prize_name"] is None
    assert data["prize_image_url"] is None


def test_complete_match_five_player_wins():
    response = client.post(
        "/api/v1/match/complete",
        json={
            "player_wins": 5,
            "buddy_wins": 0,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["winner"] == "player"
    assert data["reward_eligible"] is True
    assert data["prize_name"] == "30% Discount"


def test_complete_match_invalid_score():
    response = client.post(
        "/api/v1/match/complete",
        json={
            "player_wins": 4,
            "buddy_wins": 0,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Player wins and buddy wins must equal total games"
    )


def test_complete_match_negative_score():
    response = client.post(
        "/api/v1/match/complete",
        json={
            "player_wins": -1,
            "buddy_wins": 6,
        },
    )

    assert response.status_code == 422


def test_complete_match_missing_field():
    response = client.post(
        "/api/v1/match/complete",
        json={
            "player_wins": 4,
        },
    )

    assert response.status_code == 422

def test_login_sets_secure_session_cookie_attributes(db):
    client.cookies.clear()

    create_test_admin(db)

    response = client.post(
        "/api/v1/admin/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    set_cookie = response.headers["set-cookie"]

    assert f"{ADMIN_SESSION_COOKIE}=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Max-Age=28800" in set_cookie
    assert "Path=/" in set_cookie