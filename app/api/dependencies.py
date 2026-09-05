from collections.abc import Generator

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.admin_user import AdminUser
from app.services.auth_service import get_admin_by_session


ADMIN_SESSION_COOKIE = "nutri_admin_session"


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_admin(
    admin_session: str | None = Cookie(
        default=None,
        alias=ADMIN_SESSION_COOKIE,
    ),
    db: Session = Depends(get_db),
) -> AdminUser:
    if not admin_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    admin = get_admin_by_session(
        db=db,
        raw_token=admin_session,
    )

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return admin