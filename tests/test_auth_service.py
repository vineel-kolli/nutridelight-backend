import pytest

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models.admin_session import AdminSession

from app.models.admin_user import AdminUser

from app.services.auth_service import (
    authenticate_admin,
    create_admin_session,
    get_admin_by_session,
    hash_password,
    revoke_admin_session,
    verify_password,
    change_admin_password,
)


def test_password_hash_and_verify():
    password = "TestPassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2")
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword123!", hashed)


def test_authenticate_admin_with_valid_credentials(db):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    authenticated = authenticate_admin(
        db=db,
        username="testadmin",
        password="TestPassword123!",
    )

    assert authenticated is not None
    assert authenticated.id == admin.id
    assert authenticated.username == "testadmin"


def test_authenticate_admin_rejects_wrong_password(db):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    authenticated = authenticate_admin(
        db=db,
        username="testadmin",
        password="WrongPassword123!",
    )

    assert authenticated is None


def test_authenticate_admin_rejects_inactive_admin(db):
    admin = AdminUser(
        username="inactiveadmin",
        password_hash=hash_password("TestPassword123!"),
        is_active=False,
    )

    db.add(admin)
    db.flush()

    authenticated = authenticate_admin(
        db=db,
        username="inactiveadmin",
        password="TestPassword123!",
    )

    assert authenticated is None


def test_authenticate_admin_rejects_unknown_username(db):
    authenticated = authenticate_admin(
        db=db,
        username="doesnotexist",
        password="TestPassword123!",
    )

    assert authenticated is None


def test_create_and_resolve_admin_session(db):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    raw_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    assert raw_token
    assert len(raw_token) > 30

    resolved_admin = get_admin_by_session(
        db=db,
        raw_token=raw_token,
    )

    assert resolved_admin is not None
    assert resolved_admin.id == admin.id


def test_revoke_admin_session(db):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    raw_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    assert get_admin_by_session(
        db=db,
        raw_token=raw_token,
    ) is not None

    revoked = revoke_admin_session(
        db=db,
        raw_token=raw_token,
    )

    assert revoked is True

    assert get_admin_by_session(
        db=db,
        raw_token=raw_token,
    ) is None


def test_invalid_session_token_returns_none(db):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    assert get_admin_by_session(
        db=db,
        raw_token="invalid-token",
    ) is None

def test_expired_session_returns_none(db):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    raw_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    session = db.execute(
        select(AdminSession).where(
            AdminSession.admin_user_id == admin.id
        )
    ).scalar_one()

    session.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.flush()

    assert get_admin_by_session(
        db=db,
        raw_token=raw_token,
    ) is None


def test_inactive_admin_cannot_use_existing_session(db):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    raw_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    assert get_admin_by_session(
        db=db,
        raw_token=raw_token,
    ) is not None

    admin.is_active = False
    db.flush()

    assert get_admin_by_session(
        db=db,
        raw_token=raw_token,
    ) is None


def test_raw_session_token_is_not_stored(db):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    raw_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    session = db.execute(
        select(AdminSession).where(
            AdminSession.admin_user_id == admin.id
        )
    ).scalar_one()

    assert session.token_hash != raw_token
    assert len(session.token_hash) == 64


def test_multiple_sessions_are_independent(db):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    first_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    second_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    assert first_token != second_token

    assert get_admin_by_session(
        db=db,
        raw_token=first_token,
    ) is not None

    assert get_admin_by_session(
        db=db,
        raw_token=second_token,
    ) is not None

    revoke_admin_session(
        db=db,
        raw_token=first_token,
    )

    assert get_admin_by_session(
        db=db,
        raw_token=first_token,
    ) is None

    assert get_admin_by_session(
        db=db,
        raw_token=second_token,
    ) is not None

def test_change_admin_password(db):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password(
            "OldPassword123!"
        ),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    change_admin_password(
        db=db,
        admin_user=admin,
        current_password="OldPassword123!",
        new_password="NewPassword456!",
    )

    db.commit()

    assert verify_password(
        "NewPassword456!",
        admin.password_hash,
    )

    assert not verify_password(
        "OldPassword123!",
        admin.password_hash,
    )
def test_change_admin_password_rejects_wrong_current_password(
    db,
):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password(
            "OldPassword123!"
        ),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    with pytest.raises(
        ValueError,
        match="Current password is incorrect.",
    ):
        change_admin_password(
            db=db,
            admin_user=admin,
            current_password="WrongPassword123!",
            new_password="NewPassword456!",
        )
def test_change_admin_password_rejects_same_password(
    db,
):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password(
            "OldPassword123!"
        ),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    with pytest.raises(
        ValueError,
        match="New password must be different",
    ):
        change_admin_password(
            db=db,
            admin_user=admin,
            current_password="OldPassword123!",
            new_password="OldPassword123!",
        )

def test_change_admin_password_revokes_all_sessions(
    db,
):
    admin = AdminUser(
        username="testadmin",
        password_hash=hash_password(
            "OldPassword123!"
        ),
        is_active=True,
    )

    db.add(admin)
    db.flush()

    first_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    second_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    change_admin_password(
        db=db,
        admin_user=admin,
        current_password="OldPassword123!",
        new_password="NewPassword456!",
    )

    db.commit()

    assert get_admin_by_session(
        db=db,
        raw_token=first_token,
    ) is None

    assert get_admin_by_session(
        db=db,
        raw_token=second_token,
    ) is None