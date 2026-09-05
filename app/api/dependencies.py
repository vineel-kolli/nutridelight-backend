from collections.abc import Generator

from fastapi import (
    Cookie,
    Depends,
    Header,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.admin_user import AdminUser
from app.services.auth_service import get_admin_by_session
from app.core.config import settings

ADMIN_SESSION_COOKIE = "nutri_admin_session"

def require_admin_origin(
    origin: str | None = Header(default=None),
) -> None:
    if origin != settings.frontend_url:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid request origin",
        )
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