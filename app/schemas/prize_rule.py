from pydantic import BaseModel, Field


class PrizeRuleBase(BaseModel):
    required_wins: int = Field(
        ge=0,
        description="Number of player wins required to receive this prize.",
    )

    prize_name: str = Field(
        min_length=1,
        max_length=100,
    )

    prize_image_url: str = Field(
        min_length=1,
        max_length=500,
    )

    is_active: bool = True


class PrizeRuleCreate(PrizeRuleBase):
    pass


class PrizeRuleResponse(PrizeRuleBase):
    id: int
    game_config_id: int

    model_config = {
        "from_attributes": True,
    }
    