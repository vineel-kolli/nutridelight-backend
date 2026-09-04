from fastapi.testclient import TestClient

from app.api.dependencies import get_db
from app.core.database import SessionLocal
from app.main import app
from app.models.game_config import GameConfig
from app.models.prize_rule import PrizeRule


client = TestClient(app)


def create_test_data():
    db = SessionLocal()

    try:
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

        db.commit()

        return game_config.id

    finally:
        db.close()


def test_complete_match_four_player_wins():
    config_id = create_test_data()

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