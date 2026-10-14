import os

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.models.base import Base

# Importa os modelos para registrar suas tabelas no metadata.
import app.models  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def validate_migration_target() -> None:
    """
    Protege as migrations quando o ambiente de testes
    estiver selecionado.
    """

    if os.getenv("SGPSU_ENV_FILE") != ".env.test":
        return

    database_name = make_url(settings.database_url).database

    if database_name != "sgpsu_test":
        raise RuntimeError(
            "BLOQUEIO: o ambiente de testes exige "
            "que DATABASE_URL aponte para sgpsu_test."
        )


def run_migrations_offline() -> None:
    """Executa migrations sem abrir uma conexao."""

    validate_migration_target()

    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrations usando a conexao configurada."""

    validate_migration_target()

    migration_engine = create_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    try:
        with migration_engine.connect() as connection:

            if os.getenv("SGPSU_ENV_FILE") == ".env.test":

                connected_database = connection.execute(
                    text("SELECT current_database()")
                ).scalar_one()

                if connected_database != "sgpsu_test":
                    raise RuntimeError(
                        "BLOQUEIO: a conexao real nao esta "
                        "utilizando o banco sgpsu_test."
                    )

                # Encerra a transacao implicita aberta pelo SELECT.
                # Assim, o Alembic podera controlar sua propria transacao.
                connection.commit()

            context.configure(
                connection=connection,
                target_metadata=target_metadata,
            )

            with context.begin_transaction():
                context.run_migrations()

    finally:
        migration_engine.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()