from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.game_config import GameConfig
from app.models.prize_rule import PrizeRule
from app.schemas.prize_rule import PrizeRuleCreate


def create_prize_rule(
    db: Session,
    game_config_id: int,
    data: PrizeRuleCreate,
) -> PrizeRule:
    # Find the active game configuration.
    config_statement = select(GameConfig).where(
        GameConfig.id == game_config_id,
        GameConfig.is_active.is_(True),
    )

    game_config = db.execute(
        config_statement
    ).scalar_one_or_none()

    if game_config is None:
        raise ValueError(
            "Active game configuration not found"
        )

    # Required wins cannot be greater than total games.
    if data.required_wins > game_config.total_games:
        raise ValueError(
            "Required wins cannot exceed total games"
        )

    # Create the prize rule.
    prize_rule = PrizeRule(
        game_config_id=game_config_id,
        required_wins=data.required_wins,
        prize_name=data.prize_name,
        prize_image_url=data.prize_image_url,
        is_active=data.is_active,
    )

    db.add(prize_rule)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        print(
            "REAL DATABASE ERROR:",
            exc,
        )

        raise ValueError(
            "A prize rule already exists for this number of wins"
        ) from exc

    db.refresh(prize_rule)

    return prize_rule


def update_prize_rule(
    db: Session,
    game_config_id: int,
    prize_rule_id: int,
    data: PrizeRuleCreate,
) -> PrizeRule:

    print(
        "UPDATE CALLED:",
        game_config_id,
        prize_rule_id,
        data.model_dump(),
    )

    # ---------------------------------------------------------
    # 1. Find the active game configuration
    # ---------------------------------------------------------

    config_statement = select(GameConfig).where(
        GameConfig.id == game_config_id,
        GameConfig.is_active.is_(True),
    )

    game_config = db.execute(
        config_statement
    ).scalar_one_or_none()

    print(
        "GAME CONFIG:",
        game_config,
    )

    if game_config is None:
        raise ValueError(
            "Active game configuration not found"
        )

    # ---------------------------------------------------------
    # 2. Validate required wins
    # ---------------------------------------------------------

    if data.required_wins > game_config.total_games:
        raise ValueError(
            "Required wins cannot exceed total games"
        )

    # ---------------------------------------------------------
    # 3. Find the prize rule being updated
    # ---------------------------------------------------------

    prize_statement = select(PrizeRule).where(
        PrizeRule.id == prize_rule_id,
        PrizeRule.game_config_id == game_config_id,
    )

    prize_rule = db.execute(
        prize_statement
    ).scalar_one_or_none()

    print(
        "FOUND RULE:",
        prize_rule,
    )

    if prize_rule is None:
        raise ValueError(
            "Prize rule not found"
        )

    # ---------------------------------------------------------
    # 4. Check for another rule using the same win count
    # ---------------------------------------------------------

    duplicate_statement = select(PrizeRule).where(
        PrizeRule.game_config_id == game_config_id,
        PrizeRule.required_wins == data.required_wins,
        PrizeRule.id != prize_rule_id,
    )

    duplicate = db.execute(
        duplicate_statement
    ).scalar_one_or_none()

    print(
        "DEBUG prize_rule_id:",
        prize_rule_id,
    )

    print(
        "DEBUG current rule ID:",
        prize_rule.id,
    )

    print(
        "DEBUG requested wins:",
        data.required_wins,
    )

    print(
        "DEBUG duplicate:",
        duplicate,
    )

    if duplicate is not None:
        print(
            "DUPLICATE RULE ID:",
            duplicate.id,
        )

        print(
            "DUPLICATE RULE WINS:",
            duplicate.required_wins,
        )

        print(
            "DUPLICATE RULE NAME:",
            duplicate.prize_name,
        )

        raise ValueError(
            "A prize rule already exists for this number of wins"
        )

    # ---------------------------------------------------------
    # 5. Update the prize rule
    # ---------------------------------------------------------

    prize_rule.required_wins = data.required_wins
    prize_rule.prize_name = data.prize_name
    prize_rule.prize_image_url = data.prize_image_url
    prize_rule.is_active = data.is_active

    print("SESSION NEW:", db.new)
    print("SESSION DIRTY:", db.dirty)
    print("SESSION DELETED:", db.deleted)
    print("RULE ID:", prize_rule.id)
    print("RULE STATE:", prize_rule)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        print("REAL DATABASE ERROR:", exc)
        raise

    # ---------------------------------------------------------
    # 7. Reload updated database record
    # ---------------------------------------------------------

    db.refresh(prize_rule)

    print(
        "UPDATE SUCCESS:",
        prize_rule.id,
    )

    return prize_rule