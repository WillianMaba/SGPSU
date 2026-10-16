def auth_headers(token: str) -> dict:
    """
    Monta o cabecalho HTTP de autenticacao.
    """

    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# TESTE 1 - SOLICITANTE CONSULTA SEU CHAMADO
# ============================================================

def test_requester_can_read_own_ticket(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["own_ticket"]

    response = client.get(
        f"/tickets/{ticket.id}",
        headers=auth_headers(
            ticket_scenario["requester_token"]
        ),
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == ticket.id


# ============================================================
# TESTE 2 - SOLICITANTE NAO CONSULTA CHAMADO ALHEIO
# ============================================================

def test_requester_cannot_read_another_ticket(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["other_ticket"]

    response = client.get(
        f"/tickets/{ticket.id}",
        headers=auth_headers(
            ticket_scenario["requester_token"]
        ),
    )

    assert response.status_code == 404, response.text


# ============================================================
# TESTE 3 - ADMINISTRADOR CONSULTA QUALQUER CHAMADO
# ============================================================

def test_admin_can_read_any_ticket(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["other_ticket"]

    response = client.get(
        f"/tickets/{ticket.id}",
        headers=auth_headers(
            ticket_scenario["admin_token"]
        ),
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == ticket.id


# ============================================================
# TESTE 4 - USUARIO NAO EDITA CHAMADO NAO ATRIBUIDO
# ============================================================

def test_requester_cannot_edit_unassigned_ticket(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["own_ticket"]

    response = client.patch(
        f"/tickets/{ticket.id}",
        headers=auth_headers(
            ticket_scenario["requester_token"]
        ),
        json={
            "title": "Alteracao nao autorizada",
        },
    )

    assert response.status_code == 403, response.text


# ============================================================
# TESTE 5 - USUARIO SEM PERMISSAO NAO COMENTA
# ============================================================

def test_user_without_comment_permission_cannot_comment(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["own_ticket"]

    response = client.post(
        f"/tickets/{ticket.id}/comments",
        headers=auth_headers(
            ticket_scenario["requester_token"]
        ),
        json={
            "content": "Comentario de teste.",
        },
    )

    assert response.status_code == 403, response.text


# ============================================================
# TESTE 6 - TRANSICAO INVALIDA RETORNA 409
# ============================================================

def test_invalid_ticket_transition_returns_409(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["own_ticket"]

    response = client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_headers(
            ticket_scenario["admin_token"]
        ),
    )

    assert response.status_code == 409, response.text


# ============================================================
# TESTE 7 - LISTAGEM RESPEITA O ACESSO INDIVIDUAL
# ============================================================

def test_requester_lists_only_related_tickets(
    client,
    ticket_scenario,
):

    response = client.get(
        "/tickets/",
        headers=auth_headers(
            ticket_scenario["requester_token"]
        ),
    )

    assert response.status_code == 200, response.text

    returned_ids = {
        ticket["id"]
        for ticket in response.json()
    }

    assert ticket_scenario["own_ticket"].id in returned_ids

    assert ticket_scenario["other_ticket"].id not in returned_ids