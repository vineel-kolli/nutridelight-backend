from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column,relationship
from typing import TYPE_CHECKING

from app.core.database import Base
if TYPE_CHECKING:
    from app.models.game_config import GameConfig

class PrizeRule(Base):
    __tablename__ = "prize_rules"
    __table_args__ = (
    UniqueConstraint(
        "game_config_id",
        "required_wins",
        name="uq_prize_rule_config_wins",
    ),
)

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    game_config_id: Mapped[int] = mapped_column(
        ForeignKey("game_configs.id", ondelete="CASCADE"),
        nullable=False,
    )

    required_wins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    prize_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    prize_image_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    game_config: Mapped["GameConfig"] = relationship(
        "GameConfig",
        back_populates="prizes",
)

