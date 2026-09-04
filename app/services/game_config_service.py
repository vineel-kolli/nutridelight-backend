from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.game_config import GameConfig
from app.schemas.game_config import GameConfigCreate


def get_active_game_config(
    db: Session,
) -> GameConfig | None:
    statement = (
        select(GameConfig)
        .where(GameConfig.is_active.is_(True))
        .order_by(GameConfig.id.desc())
        .limit(1)
    )

    return db.execute(statement).scalar_one_or_none()


def update_game_config(
    db: Session,
    data: GameConfigCreate,
) -> GameConfig:
    statement = (
        select(GameConfig)
        .where(GameConfig.is_active.is_(True))
        .order_by(GameConfig.id.desc())
        .limit(1)
    )

    game_config = db.execute(statement).scalar_one_or_none()

    if game_config is None:
        game_config = GameConfig(
            id=1,
            total_games=data.total_games,
            is_active=True,
        )

        db.add(game_config)
    else:
        game_config.total_games = data.total_games
        game_config.is_active = True

    db.commit()
    db.refresh(game_config)

    return game_config