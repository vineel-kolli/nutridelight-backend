from datetime import datetime,UTC

from sqlalchemy import Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GameConfig(Base):
    __tablename__ = "game_configs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    total_games: Mapped[int] = mapped_column(
        Integer,
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
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    prizes: Mapped[list["PrizeRule"]] = relationship(
        "PrizeRule",
        back_populates="game_config",
        cascade="all, delete-orphan",   
    )