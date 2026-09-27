from sqlalchemy import text

from app.core.database import engine
from sqlalchemy.exc import IntegrityError
from datetime import datetime, UTC

import pytest

def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1")
        )

        assert result.scalar() == 1
def test_admin_login_attempt_username_ip_is_unique(db):
    from app.models.admin_login_attempt import AdminLoginAttempt

    first_attempt = AdminLoginAttempt(
        username="testadmin",
        ip_address="127.0.0.1",
        failed_attempts=1,
        last_attempt_at=datetime.now(UTC),
    )

    db.add(first_attempt)
    db.flush()

    duplicate_attempt = AdminLoginAttempt(
        username="testadmin",
        ip_address="127.0.0.1",
        failed_attempts=1,
        last_attempt_at=datetime.now(UTC),
    )

    db.add(duplicate_attempt)

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()