from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.game_config import GameConfig
from app.models.prize_rule import PrizeRule
from app.schemas.prize_rule import PrizeRuleCreate
from app.services.storage_service import (
    delete_prize_image,
    get_prize_image_storage_path,
)

DUPLICATE_PRIZE_RULE_MESSAGE = (
    "A prize rule already exists for this number of wins"
)


def create_prize_rule(
    db: Session,
    game_config_id: int,
    data: PrizeRuleCreate,
) -> PrizeRule:
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

    if data.required_wins > game_config.total_games:
        raise ValueError(
            "Required wins cannot exceed total games"
        )

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
        raise ValueError(
            DUPLICATE_PRIZE_RULE_MESSAGE
        ) from exc

    db.refresh(prize_rule)

    return prize_rule


def update_prize_rule(
    db: Session,
    game_config_id: int,
    prize_rule_id: int,
    data: PrizeRuleCreate,
) -> PrizeRule:
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

    if data.required_wins > game_config.total_games:
        raise ValueError(
            "Required wins cannot exceed total games"
        )

    prize_statement = select(PrizeRule).where(
        PrizeRule.id == prize_rule_id,
        PrizeRule.game_config_id == game_config_id,
    )

    prize_rule = db.execute(
        prize_statement
    ).scalar_one_or_none()

    if prize_rule is None:
        raise ValueError(
            "Prize rule not found"
        )

    duplicate_statement = select(PrizeRule).where(
        PrizeRule.game_config_id == game_config_id,
        PrizeRule.required_wins == data.required_wins,
        PrizeRule.id != prize_rule_id,
    )

    duplicate = db.execute(
        duplicate_statement
    ).scalar_one_or_none()

    if duplicate is not None:
        raise ValueError(
            DUPLICATE_PRIZE_RULE_MESSAGE
        )

    old_image_path = get_prize_image_storage_path(
        prize_rule.prize_image_url
    )

    new_image_path = get_prize_image_storage_path(
        data.prize_image_url
    )

    prize_rule.required_wins = data.required_wins
    prize_rule.prize_name = data.prize_name
    prize_rule.prize_image_url = data.prize_image_url
    prize_rule.is_active = data.is_active

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError(
            DUPLICATE_PRIZE_RULE_MESSAGE
        ) from exc

    db.refresh(prize_rule)

    if (
        old_image_path
        and old_image_path != new_image_path
    ):
        try:
            delete_prize_image(
                path=old_image_path
            )
        except Exception:
            # Database update succeeded.
            # Storage cleanup can be retried separately.
            pass

    return prize_rule
def get_prize_rules(
    db: Session,
    game_config_id: int,
) -> list[PrizeRule]:
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

    statement = (
        select(PrizeRule)
        .where(
            PrizeRule.game_config_id == game_config_id,
        )
        .order_by(PrizeRule.required_wins.desc())
    )

    return list(db.execute(statement).scalars().all())


def delete_prize_rule(
    db: Session,
    game_config_id: int,
    prize_rule_id: int,
) -> None:
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

    prize_statement = select(PrizeRule).where(
        PrizeRule.id == prize_rule_id,
        PrizeRule.game_config_id == game_config_id,
    )

    prize_rule = db.execute(
        prize_statement
    ).scalar_one_or_none()

    if prize_rule is None:
        raise ValueError(
            "Prize rule not found"
        )

    image_path = get_prize_image_storage_path(
    prize_rule.prize_image_url
)

    db.delete(prize_rule)
    db.commit()

    if image_path:
        try:
            delete_prize_image(
                path=image_path
            )
        except Exception:
            # Database deletion succeeded.
            # Storage cleanup can be retried separately.
            pass    