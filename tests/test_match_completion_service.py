from app.models.game_config import GameConfig
from app.models.prize_rule import PrizeRule
from app.services.match_completion_service import complete_match


def create_test_config(
    db,
    total_games: int = 5,
) -> GameConfig:
    game_config = GameConfig(
        total_games=total_games,
        is_active=True,
    )

    db.add(game_config)
    db.flush()

    return game_config


def create_test_prizes(
    db,
    game_config_id: int,
) -> None:
    db.add_all(
        [
            PrizeRule(
                game_config_id=game_config_id,
                required_wins=5,
                prize_name="30% Discount",
                prize_image_url="/30-percent.png",
                is_active=True,
            ),
            PrizeRule(
                game_config_id=game_config_id,
                required_wins=4,
                prize_name="32% Discount",
                prize_image_url="/32-percent.png",
                is_active=True,
            ),
            PrizeRule(
                game_config_id=game_config_id,
                required_wins=3,
                prize_name="Free Juice",
                prize_image_url="/free-juice.png",
                is_active=True,
            ),
        ]
    )

    db.flush()


def test_four_player_wins_get_32_percent_discount(db):
    game_config = create_test_config(db)
    create_test_prizes(db, game_config.id)

    result = complete_match(
        db=db,
        player_wins=4,
        buddy_wins=1,
    )

    assert result.total_games == 5
    assert result.player_wins == 4
    assert result.buddy_wins == 1
    assert result.winner == "player"
    assert result.reward_eligible is True
    assert result.prize_name == "32% Discount"
    assert result.prize_image_url == "/32-percent.png"


def test_three_player_wins_get_free_juice(db):
    game_config = create_test_config(db)
    create_test_prizes(db, game_config.id)

    result = complete_match(
        db=db,
        player_wins=3,
        buddy_wins=2,
    )

    assert result.total_games == 5
    assert result.winner == "player"
    assert result.reward_eligible is True
    assert result.prize_name == "Free Juice"
    assert result.prize_image_url == "/free-juice.png"


def test_two_player_wins_get_no_prize(db):
    game_config = create_test_config(db)
    create_test_prizes(db, game_config.id)

    result = complete_match(
        db=db,
        player_wins=2,
        buddy_wins=3,
    )

    assert result.total_games == 5
    assert result.winner == "buddy"
    assert result.reward_eligible is False
    assert result.prize_name is None
    assert result.prize_image_url is None


def test_five_player_wins_get_30_percent_discount(db):
    game_config = create_test_config(db)
    create_test_prizes(db, game_config.id)

    result = complete_match(
        db=db,
        player_wins=5,
        buddy_wins=0,
    )

    assert result.winner == "player"
    assert result.reward_eligible is True
    assert result.prize_name == "30% Discount"


def test_invalid_score_is_rejected(db):
    create_test_config(db)

    try:
        complete_match(
            db=db,
            player_wins=4,
            buddy_wins=0,
        )
    except ValueError as exc:
        assert str(exc) == (
            "Player wins and buddy wins must equal total games"
        )
    else:
        raise AssertionError(
            "Expected invalid score to raise ValueError"
        )


def test_no_active_game_config_is_rejected(db):
    active_configs = (
        db.query(GameConfig)
        .filter(GameConfig.is_active.is_(True))
        .all()
    )

    for config in active_configs:
        config.is_active = False

    db.flush()

    try:
        complete_match(
            db=db,
            player_wins=4,
            buddy_wins=1,
        )
    except ValueError as exc:
        assert str(exc) == "No active game configuration found"
    else:
        raise AssertionError(
            "Expected missing active config to raise ValueError"
        )


def test_inactive_prize_is_not_awarded(db):
    game_config = create_test_config(db)

    db.add(
        PrizeRule(
            game_config_id=game_config.id,
            required_wins=4,
            prize_name="32% Discount",
            prize_image_url="/32-percent.png",
            is_active=False,
        )
    )

    db.flush()

    result = complete_match(
        db=db,
        player_wins=4,
        buddy_wins=1,
    )

    assert result.winner == "player"
    assert result.reward_eligible is False
    assert result.prize_name is None