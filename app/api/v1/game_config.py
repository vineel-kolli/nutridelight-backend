from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db,get_current_admin
from app.schemas.game_config import (
    GameConfigCreate,
    GameConfigResponse,
)
from app.services.game_config_service import (
    get_active_game_config,
    update_game_config,
)


router = APIRouter(
    prefix="/game-config",
    tags=["Game Config"],
)


@router.get(
    "",
    response_model=GameConfigResponse,
)
def get_game_config(
    db: Session = Depends(get_db),
):
    game_config = get_active_game_config(db)

    if game_config is None:
        raise HTTPException(
            status_code=404,
            detail="No active game configuration found",
        )

    return game_config


@router.put(
    "",
    response_model=GameConfigResponse,
)
def update_game_config_endpoint(
    data: GameConfigCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return update_game_config(db, data)