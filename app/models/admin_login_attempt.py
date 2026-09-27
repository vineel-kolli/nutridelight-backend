from datetime import datetime

from sqlalchemy import DateTime, Integer, String,UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AdminLoginAttempt(Base):
    __tablename__ = "admin_login_attempts"
    __table_args__ = (
        UniqueConstraint(
            "username",
            "ip_address",
            name="uq_admin_login_attempt_username_ip",
        ),
    )
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        index=True,
    )

    failed_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    blocked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )