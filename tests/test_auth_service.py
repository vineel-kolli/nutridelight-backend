

from app.models.admin_user import AdminUser
from app.services.auth_service import (
    authenticate_admin,
    create_admin_session,
    get_admin_by_session,
    hash_password,
    revoke_admin_session,
    verify_password,
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