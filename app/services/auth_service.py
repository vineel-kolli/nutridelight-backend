import hashlib
import secrets
from datetime import datetime, timedelta ,UTC

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin_session import AdminSession
from app.models.admin_user import AdminUser


password_hash = PasswordHash.recommended()

SESSION_DURATION_HOURS = 8


def hash_password(password: str) -> str:
    """Hash an admin password using the recommended password hashing algorithm."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its stored hash."""
    return password_hash.verify(password, hashed_password)


def generate_session_token() -> str:
    """Generate a cryptographically secure session token."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Hash a session token before storing it in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def authenticate_admin(
    db: Session,
    username: str,
    password: str,
) -> AdminUser | None:
    """Authenticate an active admin by username and password."""

    statement = select(AdminUser).where(
        AdminUser.username == username,
        AdminUser.is_active.is_(True),
    )

    admin = db.execute(statement).scalar_one_or_none()

    if admin is None:
        return None

    if not verify_password(password, admin.password_hash):
        return None

    return admin


def create_admin_session(
    db: Session,
    admin_user: AdminUser,
) -> str:
    """Create a new admin session and return the raw token."""

    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)

    session = AdminSession(
        admin_user_id=admin_user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC)
        + timedelta(hours=SESSION_DURATION_HOURS),
    )

    db.add(session)
    db.flush()

    return raw_token


def get_admin_by_session(
    db: Session,
    raw_token: str,
) -> AdminUser | None:
    """Resolve a valid session token to its active admin user."""

    token_hash = hash_session_token(raw_token)
    now = datetime.now(UTC)

    statement = (
        select(AdminSession)
        .join(AdminUser)
        .where(
            AdminSession.token_hash == token_hash,
            AdminSession.revoked_at.is_(None),
            AdminSession.expires_at > now,
            AdminUser.is_active.is_(True),
        )
    )

    session = db.execute(statement).scalar_one_or_none()

    if session is None:
        return None

    return session.admin_user


def revoke_admin_session(
    db: Session,
    raw_token: str,
) -> bool:
    """Revoke an admin session. Returns True when a session was found."""

    token_hash = hash_session_token(raw_token)

    statement = select(AdminSession).where(
        AdminSession.token_hash == token_hash,
        AdminSession.revoked_at.is_(None),
    )

    session = db.execute(statement).scalar_one_or_none()

    if session is None:
        return False

    session.revoked_at = datetime.now(UTC)
    db.flush()

    return True

def revoke_all_admin_sessions(
    db: Session,
    admin_user_id: int,
) -> int:
    """Revoke all active sessions for an admin user."""

    statement = select(AdminSession).where(
        AdminSession.admin_user_id == admin_user_id,
        AdminSession.revoked_at.is_(None),
    )

    sessions = db.execute(statement).scalars().all()

    now = datetime.now(UTC)

    for session in sessions:
        session.revoked_at = now

    db.flush()

    return len(sessions)

def change_admin_password(
    db: Session,
    admin_user: AdminUser,
    current_password: str,
    new_password: str,
) -> None:
    """Change an admin password after verifying the current password."""

    if not verify_password(
        current_password,
        admin_user.password_hash,
    ):
        raise ValueError("Current password is incorrect.")

    if verify_password(
        new_password,
        admin_user.password_hash,
    ):
        raise ValueError(
            "New password must be different from the current password."
        )

    admin_user.password_hash = hash_password(new_password)

    revoke_all_admin_sessions(
        db=db,
        admin_user_id=admin_user.id,
    )

    db.flush()