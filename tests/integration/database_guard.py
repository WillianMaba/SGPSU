from sqlalchemy.engine import make_url


TEST_DATABASE_NAME = "sgpsu_test"


def validate_test_database(database_url: str) -> None:

    url = make_url(database_url)

    database_name = url.database

    if database_name != TEST_DATABASE_NAME:
        raise RuntimeError(
            "BLOQUEIO DE SEGURANCA: os testes de integracao "
            f"exigem o banco '{TEST_DATABASE_NAME}', "
            f"mas a configuracao aponta para '{database_name}'."
        )