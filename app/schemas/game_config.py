from pydantic import BaseModel, Field,field_validator

from app.schemas.prize_rule import PrizeRuleResponse


class GameConfigBase(BaseModel):
    total_games: int = Field(
        ge=1,
        le=99,
        description="Number of games in one match.Must be odd",
    )
    @field_validator("total_games")
    @classmethod
    def validate_total_games(cls, value: int) -> int:
        if value % 2 == 0:
            raise ValueError("total_games must be an odd number")
        return value


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