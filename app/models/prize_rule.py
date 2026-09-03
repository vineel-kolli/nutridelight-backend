from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PrizeRule(Base):
    __tablename__ = "prize_rules"

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
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    