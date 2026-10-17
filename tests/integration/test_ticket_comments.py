from app.models.ticket_comment import TicketComment


def auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}"
    }


def test_admin_can_add_comment(
    client,
    ticket_scenario,
    db_session,
):
    scenario = ticket_scenario
    ticket = scenario["own_ticket"]

    response = client.post(
        f"/tickets/{ticket.id}/comments",
        headers=auth_headers(scenario["admin_token"]),
        json={
            "content": "  Atendimento em analise.  ",
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["ticket_id"] == ticket.id
    assert data["user_id"] == scenario["admin"].id
    assert data["content"] == "Atendimento em analise."

    saved_comment = db_session.get(
        TicketComment,
        data["id"],
    )

    assert saved_comment is not None


def test_requester_can_list_comments_on_own_ticket(
    client,
    ticket_scenario,
):
    scenario = ticket_scenario
    ticket = scenario["own_ticket"]

    # Administrador adiciona um comentario.
    created = client.post(
        f"/tickets/{ticket.id}/comments",
        headers=auth_headers(scenario["admin_token"]),
        json={
            "content": "Verificando a solicitacao.",
        },
    )

    assert created.status_code == 201, created.text

    # O solicitante consulta os comentarios do proprio chamado.
    response = client.get(
        f"/tickets/{ticket.id}/comments",
        headers=auth_headers(scenario["requester_token"]),
    )

    assert response.status_code == 200, response.text

    contents = [
        comment["content"]
        for comment in response.json()
    ]

    assert "Verificando a solicitacao." in contents


def test_comment_creates_history_entry(
    client,
    ticket_scenario,
):
    scenario = ticket_scenario
    ticket = scenario["own_ticket"]

    created = client.post(
        f"/tickets/{ticket.id}/comments",
        headers=auth_headers(scenario["admin_token"]),
        json={
            "content": "Comentario com registro de historico.",
        },
    )

    assert created.status_code == 201, created.text

    response = client.get(
        f"/tickets/{ticket.id}/history",
        headers=auth_headers(scenario["admin_token"]),
    )

    assert response.status_code == 200, response.text

    actions = [
        entry["action"]
        for entry in response.json()
    ]

    assert "comment_added" in actions


def test_user_cannot_read_comments_from_another_ticket(
    client,
    ticket_scenario,
):
    scenario = ticket_scenario

    response = client.get(
        f'/tickets/{scenario["other_ticket"].id}/comments',
        headers=auth_headers(scenario["requester_token"]),
    )

    assert response.status_code == 404, response.text