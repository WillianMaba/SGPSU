import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from tests.integration.database_guard import validate_test_database


# Protecao antes de importar a aplicacao.
if os.getenv("SGPSU_ENV_FILE") != ".env.test":
    raise RuntimeError(
        "BLOQUEIO: os testes de integracao exigem "
        "SGPSU_ENV_FILE=.env.test."
    )


from app.core.config import settings  # noqa: E402

validate_test_database(settings.database_url)

from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def test_engine():

    engine = create_engine(settings.database_url)

    try:
        with engine.connect() as connection:

            database_name = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

            if database_name != "sgpsu_test":
                raise RuntimeError(
                    "BLOQUEIO: conexao realizada com o banco errado."
                )

            migration_table = connection.execute(
                text("SELECT to_regclass('public.alembic_version')")
            ).scalar_one()

            if migration_table is None:
                raise RuntimeError(
                    "O banco de testes ainda nao recebeu as migrations."
                )

        yield engine

    finally:
        engine.dispose()


@pytest.fixture
def db_session(test_engine):

    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session

    finally:
        session.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()


@pytest.fixture
def client(db_session):

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.pop(get_db, None)