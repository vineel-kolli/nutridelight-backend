import pytest

from app.services.reward_engine import (
    RewardResult,
    RewardRule,
    calculate_reward,
)


@pytest.fixture
def prize_rules() -> list[RewardRule]:
    return [
        RewardRule(
            required_wins=5,
            prize_name="30% Discount",
            prize_image_url="/30-percent.png",
        ),
        RewardRule(
            required_wins=4,
            prize_name="32% Discount",
            prize_image_url="/32-percent.png",
        ),
        RewardRule(
            required_wins=3,
            prize_name="Free Juice",
            prize_image_url="/free-juice.png",
        ),
    ]


def test_five_player_wins_get_30_percent_discount(
    prize_rules: list[RewardRule],
) -> None:
    result = calculate_reward(
        player_wins=5,
        buddy_wins=0,
        total_games=5,
        prize_rules=prize_rules,
    )

    assert result == RewardResult(
        eligible=True,
        prize_name="30% Discount",
        prize_image_url="/30-percent.png",
        required_wins=5,
    )


def test_four_player_wins_get_32_percent_discount(
    prize_rules: list[RewardRule],
) -> None:
    result = calculate_reward(
        player_wins=4,
        buddy_wins=1,
        total_games=5,
        prize_rules=prize_rules,
    )

    assert result == RewardResult(
        eligible=True,
        prize_name="32% Discount",
        prize_image_url="/32-percent.png",
        required_wins=4,
    )


def test_three_player_wins_get_free_juice(
    prize_rules: list[RewardRule],
) -> None:
    result = calculate_reward(
        player_wins=3,
        buddy_wins=2,
        total_games=5,
        prize_rules=prize_rules,
    )

    assert result == RewardResult(
        eligible=True,
        prize_name="Free Juice",
        prize_image_url="/free-juice.png",
        required_wins=3,
    )


@pytest.mark.parametrize(
    "player_wins,buddy_wins",
    [
        (2, 3),
        (1, 4),
        (0, 5),
    ],
)
def test_two_or_fewer_player_wins_get_no_prize(
    player_wins: int,
    buddy_wins: int,
    prize_rules: list[RewardRule],
) -> None:
    result = calculate_reward(
        player_wins=player_wins,
        buddy_wins=buddy_wins,
        total_games=5,
        prize_rules=prize_rules,
    )

    assert result == RewardResult(
        eligible=False,
        prize_name=None,
        prize_image_url=None,
        required_wins=None,
    )


def test_inactive_prize_rule_is_not_eligible() -> None:
    rules = [
        RewardRule(
            required_wins=5,
            prize_name="30% Discount",
            prize_image_url="/30-percent.png",
            is_active=False,
        )
    ]

    result = calculate_reward(
        player_wins=5,
        buddy_wins=0,
        total_games=5,
        prize_rules=rules,
    )

    assert result.eligible is False


def test_prize_rule_order_does_not_matter() -> None:
    rules = [
        RewardRule(
            required_wins=3,
            prize_name="Free Juice",
            prize_image_url="/free-juice.png",
        ),
        RewardRule(
            required_wins=5,
            prize_name="30% Discount",
            prize_image_url="/30-percent.png",
        ),
        RewardRule(
            required_wins=4,
            prize_name="32% Discount",
            prize_image_url="/32-percent.png",
        ),
    ]

    result = calculate_reward(
        player_wins=4,
        buddy_wins=1,
        total_games=5,
        prize_rules=rules,
    )

    assert result.prize_name == "32% Discount"
    assert result.required_wins == 4


@pytest.mark.parametrize("total_games", [0, -1])
def test_total_games_must_be_positive(
    total_games: int,
    prize_rules: list[RewardRule],
) -> None:
    with pytest.raises(ValueError, match="total_games must be at least 1"):
        calculate_reward(
            player_wins=0,
            buddy_wins=0,
            total_games=total_games,
            prize_rules=prize_rules,
        )


@pytest.mark.parametrize("total_games", [2, 4, 6])
def test_total_games_must_be_odd(
    total_games: int,
    prize_rules: list[RewardRule],
) -> None:
    with pytest.raises(ValueError, match="total_games must be an odd number"):
        calculate_reward(
            player_wins=1,
            buddy_wins=1,
            total_games=total_games,
            prize_rules=prize_rules,
        )


def test_negative_scores_are_rejected(
    prize_rules: list[RewardRule],
) -> None:
    with pytest.raises(ValueError, match="Scores cannot be negative"):
        calculate_reward(
            player_wins=-1,
            buddy_wins=6,
            total_games=5,
            prize_rules=prize_rules,
        )


def test_scores_must_equal_total_games(
    prize_rules: list[RewardRule],
) -> None:
    with pytest.raises(
        ValueError,
        match="Player wins and buddy wins must equal total games",
    ):
        calculate_reward(
            player_wins=4,
            buddy_wins=0,
            total_games=5,
            prize_rules=prize_rules,
        )