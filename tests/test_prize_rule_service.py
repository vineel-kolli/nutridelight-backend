import pytest
from app.models.game_config import GameConfig
from app.models.prize_rule import PrizeRule
from app.schemas.prize_rule import PrizeRuleCreate
from app.schemas.game_config import GameConfigCreate
from app.services.game_config_service import update_game_config
from app.services.prize_rule_service import (
    create_prize_rule,
    update_prize_rule,
    get_prize_rules,
)


def create_game_config(
    db,
    total_games: int = 5,
    is_active: bool = True,
) -> GameConfig:
    game_config = GameConfig(
        total_games=total_games,
        is_active=is_active,
    )

    db.add(game_config)
    db.flush()

    return game_config


def create_prize(
    db,
    game_config_id: int,
    required_wins: int = 5,
    prize_name: str = "30% Discount",
) -> PrizeRule:
    prize_rule = PrizeRule(
        game_config_id=game_config_id,
        required_wins=required_wins,
        prize_name=prize_name,
        prize_image_url="https://example.com/prize.png",
        is_active=True,
    )

    db.add(prize_rule)
    db.flush()

    return prize_rule


def prize_data(
    required_wins: int = 5,
    prize_name: str = "30% Discount",
) -> PrizeRuleCreate:
    return PrizeRuleCreate(
        required_wins=required_wins,
        prize_name=prize_name,
        prize_image_url="https://example.com/prize.png",
        is_active=True,
    )


def test_create_prize_rule_success(db):
    game_config = create_game_config(db)

    rule = create_prize_rule(
        db=db,
        game_config_id=game_config.id,
        data=prize_data(),
    )

    assert rule.id is not None
    assert rule.game_config_id == game_config.id
    assert rule.required_wins == 5
    assert rule.prize_name == "30% Discount"
    assert rule.is_active is True


def test_create_prize_rule_rejects_missing_config(db):
    data = prize_data()

    try:
        create_prize_rule(
            db=db,
            game_config_id=999999,
            data=data,
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Active game configuration not found"


def test_create_prize_rule_rejects_inactive_config(db):
    game_config = create_game_config(
        db,
        is_active=False,
    )

    try:
        create_prize_rule(
            db=db,
            game_config_id=game_config.id,
            data=prize_data(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Active game configuration not found"


def test_create_prize_rule_rejects_wins_above_total_games(db):
    game_config = create_game_config(
        db,
        total_games=5,
    )

    try:
        create_prize_rule(
            db=db,
            game_config_id=game_config.id,
            data=prize_data(required_wins=6),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Required wins cannot exceed total games"


def test_create_prize_rule_rejects_duplicate_required_wins(db):
    game_config = create_game_config(db)

    create_prize_rule(
        db=db,
        game_config_id=game_config.id,
        data=prize_data(required_wins=5),
    )

    try:
        create_prize_rule(
            db=db,
            game_config_id=game_config.id,
            data=prize_data(
                required_wins=5,
                prize_name="Another Prize",
            ),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == (
            "A prize rule already exists for this number of wins"
        )


def test_update_prize_rule_success(db):
    game_config = create_game_config(db)

    rule = create_prize(
        db=db,
        game_config_id=game_config.id,
    )

    updated = update_prize_rule(
        db=db,
        game_config_id=game_config.id,
        prize_rule_id=rule.id,
        data=prize_data(
            required_wins=4,
            prize_name="32% Discount",
        ),
    )

    assert updated.id == rule.id
    assert updated.game_config_id == game_config.id
    assert updated.required_wins == 4
    assert updated.prize_name == "32% Discount"
    assert updated.prize_image_url == "https://example.com/prize.png"
    assert updated.is_active is True


def test_update_prize_rule_rejects_missing_config(db):
    game_config = create_game_config(db)

    rule = create_prize(
        db=db,
        game_config_id=game_config.id,
    )

    try:
        update_prize_rule(
            db=db,
            game_config_id=999999,
            prize_rule_id=rule.id,
            data=prize_data(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Active game configuration not found"


def test_update_prize_rule_rejects_missing_rule(db):
    game_config = create_game_config(db)

    try:
        update_prize_rule(
            db=db,
            game_config_id=game_config.id,
            prize_rule_id=999999,
            data=prize_data(),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Prize rule not found"


def test_update_prize_rule_rejects_wins_above_total_games(db):
    game_config = create_game_config(
        db,
        total_games=5,
    )

    rule = create_prize(
        db=db,
        game_config_id=game_config.id,
    )

    try:
        update_prize_rule(
            db=db,
            game_config_id=game_config.id,
            prize_rule_id=rule.id,
            data=prize_data(required_wins=6),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Required wins cannot exceed total games"


def test_update_prize_rule_rejects_duplicate_required_wins(db):
    game_config = create_game_config(db)

    first_rule = create_prize(
        db=db,
        game_config_id=game_config.id,
        required_wins=5,
        prize_name="30% Discount",
    )

    second_rule = create_prize(
        db=db,
        game_config_id=game_config.id,
        required_wins=4,
        prize_name="32% Discount",
    )

    try:
        update_prize_rule(
            db=db,
            game_config_id=game_config.id,
            prize_rule_id=second_rule.id,
            data=prize_data(
                required_wins=first_rule.required_wins,
                prize_name="Duplicate Prize",
            ),
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == (
            "A prize rule already exists for this number of wins"
        )


def test_get_prize_rules_returns_rules_sorted_by_required_wins(db):
    game_config = create_game_config(
        db,
        total_games=5,
    )

    create_prize(
        db,
        game_config_id=game_config.id,
        required_wins=3,
    )

    create_prize(
        db,
        game_config_id=game_config.id,
        required_wins=5,
    )

    create_prize(
        db,
        game_config_id=game_config.id,
        required_wins=4,
    )

    rules = get_prize_rules(
        db,
        game_config.id,
    )

    assert [rule.required_wins for rule in rules] == [
        5,
        4,
        3,
    ]


def test_get_prize_rules_rejects_missing_config(db):
    with pytest.raises(
        ValueError,
        match="Active game configuration not found",
    ):
        get_prize_rules(
            db,
            game_config_id=999999,
        )


def test_update_game_config_rejects_total_games_below_existing_prize_rule(
    db,
):
    game_config = create_game_config(
        db,
        total_games=5,
    )

    create_prize(
        db,
        game_config_id=game_config.id,
        required_wins=5,
    )

    with pytest.raises(
        ValueError,
        match="Total games cannot be lower than an existing prize rule's required wins",
    ):
        update_game_config(
            db,
            GameConfigCreate(total_games=3),
        )

    db.refresh(game_config)

    assert game_config.total_games == 5


def test_update_game_config_allows_total_games_when_prize_rules_remain_valid(
    db,
):
    game_config = create_game_config(
        db,
        total_games=5,
    )

    create_prize(
        db,
        game_config_id=game_config.id,
        required_wins=3,
    )

    updated_config = update_game_config(
        db,
        GameConfigCreate(total_games=3),
    )

    assert updated_config.id == game_config.id
    assert updated_config.total_games == 3