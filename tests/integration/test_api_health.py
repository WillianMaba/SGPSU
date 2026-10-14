from sqlalchemy import text


def test_connected_database_is_test_database(db_session):

    result = db_session.execute(
        text("SELECT current_database()")
    ).scalar_one()

    assert result == "sgpsu_test"


def test_root_endpoint_returns_200(client):

    response = client.get("/")

    assert response.status_code == 200


def test_ticket_list_requires_authentication(client):

    response = client.get("/tickets/")

    assert response.status_code == 401


def test_ticket_details_require_authentication(client):

    response = client.get("/tickets/1")

    assert response.status_code == 401


def test_ticket_history_requires_authentication(client):

    response = client.get("/tickets/1/history")

    assert response.status_code == 401