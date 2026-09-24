from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.game_config import GameConfig
from app.models.prize_rule import PrizeRule
from app.schemas.game_config import GameConfigCreate


def get_active_game_config(db: Session) -> GameConfig | None:
    statement = (
        select(GameConfig)
        .where(GameConfig.is_active.is_(True))
        .order_by(GameConfig.id.asc())
    )

    configs = db.execute(statement).scalars().all()

    if not configs:
        return None

    if len(configs) > 1:
        raise RuntimeError(
            "Database integrity error: multiple active game configurations exist"
        )

    return configs[0]


def update_game_config(
    db: Session,
    data: GameConfigCreate,
) -> GameConfig:
    game_config = get_active_game_config(db)

    if game_config is None:
        game_config = GameConfig(
            total_games=data.total_games,
            is_active=True,
        )

        db.add(game_config)
        db.commit()
        db.refresh(game_config)

        return game_config

    invalid_rule_statement = (
        select(PrizeRule)
        .where(
            PrizeRule.game_config_id == game_config.id,
            PrizeRule.required_wins > data.total_games,
        )
        .limit(1)
    )

    invalid_rule = db.execute(
        invalid_rule_statement
    ).scalar_one_or_none()

    if invalid_rule is not None:
        raise ValueError(
            "Total games cannot be lower than an existing prize rule's required wins"
        )

    game_config.total_games = data.total_games

    db.commit()
    db.refresh(game_config)

    return game_config