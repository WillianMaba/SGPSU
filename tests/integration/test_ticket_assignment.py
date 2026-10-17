def auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}"
    }


def test_admin_can_assign_ticket_and_create_history(
    client,
    ticket_scenario,
):
    scenario = ticket_scenario
    ticket = scenario["own_ticket"]
    admin = scenario["admin"]

    # 1. Administrador atribui o chamado a si mesmo.
    response = client.patch(
        f"/tickets/{ticket.id}",
        headers=auth_headers(scenario["admin_token"]),
        json={
            "assignee_id": admin.id,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["assignee_id"] == admin.id

    # 2. Confirma que o historico registrou a atribuicao.
    history = client.get(
        f"/tickets/{ticket.id}/history",
        headers=auth_headers(scenario["admin_token"]),
    )

    assert history.status_code == 200, history.text

    actions = [
        entry["action"]
        for entry in history.json()
    ]

    assert "assigned" in actions


def test_assignee_without_assign_permission_cannot_reassign_ticket(
    client,
    ticket_scenario,
):
    scenario = ticket_scenario
    ticket = scenario["own_ticket"]

    admin_headers = auth_headers(
        scenario["admin_token"]
    )

    requester_headers = auth_headers(
        scenario["requester_token"]
    )

    # 1. Administrador atribui o chamado ao solicitante.
    assignment = client.patch(
        f"/tickets/{ticket.id}",
        headers=admin_headers,
        json={
            "assignee_id": scenario["requester"].id,
        },
    )

    assert assignment.status_code == 200, assignment.text

    # 2. O usuario agora e responsavel pelo chamado,
    # mas continua sem possuir tickets.assign.
    response = client.patch(
        f"/tickets/{ticket.id}",
        headers=requester_headers,
        json={
            "assignee_id": scenario["admin"].id,
        },
    )

    assert response.status_code == 403, response.text

    # 3. A tentativa negada nao pode mudar o responsavel.
    verification = client.get(
        f"/tickets/{ticket.id}",
        headers=admin_headers,
    )

    assert verification.status_code == 200, verification.text

    assert (
        verification.json()["assignee_id"]
        == scenario["requester"].id
    )