from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.game_config import GameConfig
from app.models.prize_rule import PrizeRule
from app.schemas.match import MatchCompletionResponse
from app.services.reward_engine import RewardRule, calculate_reward


def complete_match(
    db: Session,
    player_wins: int,
    buddy_wins: int,
) -> MatchCompletionResponse:
    """
    Validate a completed match and calculate the player's reward.

    The match itself is not persisted. The kiosk owns the temporary
    game state and submits the final score once the match is complete.
    """

    # ---------------------------------------------------------
    # 1. Load the active game configuration
    # ---------------------------------------------------------

    config_statement = (
        select(GameConfig)
        .where(GameConfig.is_active.is_(True))
        .order_by(GameConfig.id.desc())
        .limit(1)
    )

    game_config = db.execute(
        config_statement
    ).scalar_one_or_none()

    if game_config is None:
        raise ValueError(
            "No active game configuration found"
        )

    total_games = game_config.total_games

    # ---------------------------------------------------------
    # 2. Validate the configured number of games
    # ---------------------------------------------------------

    if total_games < 1:
        raise ValueError(
            "Game configuration must contain at least one game"
        )

    if total_games % 2 == 0:
        raise ValueError(
            "Game configuration must contain an odd number of games"
        )

    # ---------------------------------------------------------
    # 3. Validate the submitted score
    # ---------------------------------------------------------

    if player_wins < 0 or buddy_wins < 0:
        raise ValueError(
            "Scores cannot be negative"
        )

    if player_wins + buddy_wins != total_games:
        raise ValueError(
            "Player wins and buddy wins must equal total games"
        )

    if player_wins == buddy_wins:
        raise ValueError(
            "A completed match cannot end in a tie"
        )

    # ---------------------------------------------------------
    # 4. Determine the match winner
    # ---------------------------------------------------------

    winner = (
        "player"
        if player_wins > buddy_wins
        else "buddy"
    )

    # ---------------------------------------------------------
    # 5. Load active prize rules
    # ---------------------------------------------------------

    prize_statement = (
        select(PrizeRule)
        .where(
            PrizeRule.game_config_id == game_config.id,
            PrizeRule.is_active.is_(True),
        )
    )

    prize_rules = db.execute(
        prize_statement
    ).scalars().all()

    # Convert database models into pure reward-engine inputs.
    reward_rules = [
        RewardRule(
            required_wins=rule.required_wins,
            prize_name=rule.prize_name,
            prize_image_url=rule.prize_image_url,
            is_active=rule.is_active,
        )
        for rule in prize_rules
    ]

    # ---------------------------------------------------------
    # 6. Calculate reward
    # ---------------------------------------------------------

    reward = calculate_reward(
        player_wins=player_wins,
        buddy_wins=buddy_wins,
        total_games=total_games,
        prize_rules=reward_rules,
    )

    # ---------------------------------------------------------
    # 7. Return final result
    # ---------------------------------------------------------

    return MatchCompletionResponse(
        total_games=total_games,
        player_wins=player_wins,
        buddy_wins=buddy_wins,
        winner=winner,
        reward_eligible=reward.eligible,
        prize_name=reward.prize_name,
        prize_image_url=reward.prize_image_url,
    )