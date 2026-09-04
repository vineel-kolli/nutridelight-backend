from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class RewardRule:
    required_wins: int
    prize_name: str
    prize_image_url: str
    is_active: bool = True


@dataclass(frozen=True)
class RewardResult:
    eligible: bool
    prize_name: str | None
    prize_image_url: str | None
    required_wins: int | None


def calculate_reward(
    *,
    player_wins: int,
    buddy_wins: int,
    total_games: int,
    prize_rules: Sequence[RewardRule],
) -> RewardResult:
    """
    Determine the reward earned from a completed match.

    Business rules:
    - total_games must be a positive odd number.
    - player_wins and buddy_wins cannot be negative.
    - player_wins + buddy_wins must equal total_games.
    - only active prize rules are eligible.
    - the prize rule with required_wins exactly equal to
      player_wins is selected.
    - if no matching active rule exists, there is no prize.
    """

    if total_games < 1:
        raise ValueError("total_games must be at least 1")

    if total_games % 2 == 0:
        raise ValueError("total_games must be an odd number")

    if player_wins < 0 or buddy_wins < 0:
        raise ValueError("Scores cannot be negative")

    if player_wins + buddy_wins != total_games:
        raise ValueError(
            "Player wins and buddy wins must equal total games"
        )

    matching_rule: RewardRule | None = None

    for rule in prize_rules:
        if not rule.is_active:
            continue

        if rule.required_wins == player_wins:
            matching_rule = rule
            break

    if matching_rule is None:
        return RewardResult(
            eligible=False,
            prize_name=None,
            prize_image_url=None,
            required_wins=None,
        )

    return RewardResult(
        eligible=True,
        prize_name=matching_rule.prize_name,
        prize_image_url=matching_rule.prize_image_url,
        required_wins=matching_rule.required_wins,
    )