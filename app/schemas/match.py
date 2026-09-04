from pydantic import BaseModel, Field


class MatchCompletionRequest(BaseModel):
    player_wins: int = Field(
        ge=0,
        description="Number of counted games won by the player.",
    )

    buddy_wins: int = Field(
        ge=0,
        description="Number of counted games won by the buddy.",
    )


class MatchCompletionResponse(BaseModel):
    total_games: int
    player_wins: int
    buddy_wins: int
    winner: str
    reward_eligible: bool
    prize_name: str | None
    prize_image_url: str | None