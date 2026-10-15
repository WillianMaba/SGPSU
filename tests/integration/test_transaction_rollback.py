from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.sector import Sector


def test_external_transaction_rolls_back_after_commit(
    test_engine,
):
    """
    Confirma que o commit realizado dentro de um savepoint
    nao confirma a transacao externa do teste.
    """

    unique_name = f"Rollback Test {uuid4().hex}"

    # Abrimos uma conexao exclusiva.
    with test_engine.connect() as connection:

        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        assert database_name == "sgpsu_test"

        # A consulta anterior iniciou uma transacao implicita.
        # Vamos utiliza-la como nossa transacao externa.
        transaction = connection.get_transaction()

        session = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        )

        try:

            sector = Sector(
                name=unique_name,
                description="Teste de rollback.",
                is_active=True,
            )

            session.add(sector)

            # Este commit pertence a sessao do teste.
            session.commit()

            # Dentro da mesma transacao, o registro existe.
            saved_sector = session.scalar(
                select(Sector).where(
                    Sector.name == unique_name
                )
            )

            assert saved_sector is not None

        finally:

            session.close()

            # Desfaz a transacao externa.
            transaction.rollback()

    # Abrimos outra conexao para verificar se o dado persistiu.
    with test_engine.connect() as verification_connection:

        saved_sector = verification_connection.scalar(
            select(Sector).where(
                Sector.name == unique_name
            )
        )

        assert saved_sector is None