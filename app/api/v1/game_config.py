from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.admin_user import AdminUser

from app.api.dependencies import (
    get_current_admin,
    get_db,
    require_admin_origin,
)
from app.schemas.game_config import (
    GameConfigCreate,
    GameConfigResponse,
)
from app.services.game_config_service import (
    get_active_game_config,
    update_game_config,
)
import logging

logger = logging.getLogger(__name__)

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
    try:
        game_config = get_active_game_config(db)
    except RuntimeError as exc:
        logger.exception("Failed to retrieve active game configuration")
        raise HTTPException(
            status_code=500,
            detail="Game configuration temporarily unavailable",
        ) from exc

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
    admin: AdminUser = Depends(get_current_admin),
    _: None = Depends(require_admin_origin),
):
    try:
        return update_game_config(db, data)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        logger.exception("Failed to update game configuration")
        raise HTTPException(
            status_code=500,
            detail="Game configuration temporarily unavailable",
        ) from exc