from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

from app.api.v1.health import router as health_router
from app.api.v1.game_config import router as game_config_router
from app.api.v1.prize_rule import router as prize_rule_router
from app.api.v1.match import router as match_router

from app.api.v1.admin_auth import router as admin_auth_router

app = FastAPI(title=settings.app_name,version=settings.app_version,)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(health_router,prefix="/api/v1",)

app.include_router( game_config_router,prefix="/api/v1",)

app.include_router(prize_rule_router,prefix="/api/v1",)

app.include_router(match_router,prefix="/api/v1",)

app.include_router(admin_auth_router, prefix="/api/v1",)