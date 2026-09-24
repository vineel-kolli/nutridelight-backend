from datetime import datetime, timedelta, UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin_login_attempt import AdminLoginAttempt


MAX_FAILED_ATTEMPTS = 5
BLOCK_DURATION_MINUTES = 15


def get_attempt(
    db: Session,
    username: str,
    ip_address: str,
) -> AdminLoginAttempt | None:
    statement = select(AdminLoginAttempt).where(
        AdminLoginAttempt.username == username,
        AdminLoginAttempt.ip_address == ip_address,
    )

    return db.execute(statement).scalar_one_or_none()


def is_login_blocked(
    db: Session,
    username: str,
    ip_address: str,
) -> bool:
    attempt = get_attempt(
        db=db,
        username=username,
        ip_address=ip_address,
    )

    if attempt is None:
        return False

    if attempt.blocked_until is None:
        return False

    now = datetime.now(UTC)

    if attempt.blocked_until <= now:
        attempt.blocked_until = None
        attempt.failed_attempts = 0
        db.flush()
        return False

    return True


def record_failed_login(
    db: Session,
    username: str,
    ip_address: str,
) -> None:
    now = datetime.now(UTC)

    attempt = get_attempt(
        db=db,
        username=username,
        ip_address=ip_address,
    )

    if attempt is None:
        attempt = AdminLoginAttempt(
            username=username,
            ip_address=ip_address,
            failed_attempts=1,
            last_attempt_at=now,
        )

        db.add(attempt)
        db.flush()
        return

    attempt.failed_attempts += 1
    attempt.last_attempt_at = now

    if attempt.failed_attempts >= MAX_FAILED_ATTEMPTS:
        attempt.blocked_until = (
            now + timedelta(minutes=BLOCK_DURATION_MINUTES)
        )

    db.flush()


def reset_failed_logins(
    db: Session,
    username: str,
    ip_address: str,
) -> None:
    attempt = get_attempt(
        db=db,
        username=username,
        ip_address=ip_address,
    )

    if attempt is None:
        return

    db.delete(attempt)
    db.flush()