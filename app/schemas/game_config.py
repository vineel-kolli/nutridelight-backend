from pydantic import BaseModel, Field

from app.schemas.prize_rule import PrizeRuleResponse


class GameConfigBase(BaseModel):
    total_games: int = Field(
        ge=1,
        le=100,
        description="Number of games in one match.",
    )

    is_active: bool = True


class GameConfigCreate(GameConfigBase):
    pass


class GameConfigResponse(GameConfigBase):
    id: int
    prizes: list[PrizeRuleResponse] = Field(
        default_factory=list
    )

    model_config = {
        "from_attributes": True,
    }