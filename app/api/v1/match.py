from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.match import (
    MatchCompletionRequest,
    MatchCompletionResponse,
)
from app.services.match_completion_service import complete_match


router = APIRouter(
    prefix="/match",
    tags=["Match"],
)


@router.post(
    "/complete",
    response_model=MatchCompletionResponse,
)
def complete_match_endpoint(
    data: MatchCompletionRequest,
    db: Session = Depends(get_db),
):
    try:
        return complete_match(
            db=db,
            player_wins=data.player_wins,
            buddy_wins=data.buddy_wins,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc