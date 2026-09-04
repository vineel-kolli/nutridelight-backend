from fastapi import FastAPI

from app.core.config import settings

from app.api.v1.health import router as health_router
from app.api.v1.game_config import router as game_config_router
from app.api.v1.prize_rule import router as prize_rule_router

app = FastAPI(
    title= settings.app_name,
    version=settings.app_version,
)

app.include_router(
    health_router,
    prefix="/api/v1",
)

app.include_router(
    game_config_router,
    prefix="/api/v1",
)

app.include_router(
    prize_rule_router,
    prefix="/api/v1",
)