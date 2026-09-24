import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.database import engine
from app.main import app
from app.models.game_config import GameConfig


@pytest.fixture(autouse=True)
def db():
    """
    Give every test an isolated SQLAlchemy session.

    All test changes happen inside one outer transaction.
    Even if application code calls db.commit(), the outer
    transaction remains active because the session uses a SAVEPOINT.

    At the end of the test, the outer transaction is rolled back.

    This means tests use the same PostgreSQL database as development,
    but test data does not permanently modify development data.
    """

    connection = engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    # Hide production active configs inside this transaction.
    #
    # This prevents tests that create their own active GameConfig
    # from seeing the real development config at the same time.
    #
    # The change is rolled back after the test.
    session.execute(
        update(GameConfig)
        .where(GameConfig.is_active.is_(True))
        .values(is_active=False)
    )

    session.flush()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield session

    finally:
        app.dependency_overrides.pop(get_db, None)

        session.close()

        transaction.rollback()
        connection.close()