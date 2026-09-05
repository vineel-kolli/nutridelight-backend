from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db,get_current_admin
from app.schemas.prize_rule import (
    PrizeRuleCreate,
    PrizeRuleResponse,
)
from app.services.prize_rule_service import (
    create_prize_rule,
    update_prize_rule,
)


router = APIRouter(
    prefix="/game-config/{game_config_id}/prize-rules",
    tags=["Prize Rules"],
)


@router.post(
    "",
    response_model=PrizeRuleResponse,
    status_code=201,
)
def create_prize_rule_endpoint(
    game_config_id: int,
    data: PrizeRuleCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    try:
        return create_prize_rule(
            db,
            game_config_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.put(
    "/{prize_rule_id}",
    response_model=PrizeRuleResponse,
)
def update_prize_rule_endpoint(
    game_config_id: int,
    prize_rule_id: int,
    data: PrizeRuleCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),

):
    try:
        return update_prize_rule(
            db,
            game_config_id,
            prize_rule_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc