def auth_headers(token: str) -> dict:
    """
    Monta o cabecalho de autenticacao.
    """

    return {
        "Authorization": f"Bearer {token}"
    }


def ticket_payload(scenario: dict) -> dict:
    """
    Prepara os dados necessarios para abrir um chamado.
    Utiliza os IDs reais gerados pelo banco de testes.
    """

    return {
        "title": "Falha de acesso ao sistema",
        "description": "Usuario nao consegue acessar o sistema.",
        "status_id": scenario["statuses"]["Aberto"].id,
        "priority_id": scenario["priority"].id,
        "category_id": scenario["category"].id,
    }


# ============================================================
# TESTE 1 - CICLO COMPLETO DO CHAMADO
# ============================================================

def test_complete_ticket_lifecycle(
    client,
    ticket_scenario,
):

    scenario = ticket_scenario

    requester_headers = auth_headers(
        scenario["requester_token"]
    )

    admin_headers = auth_headers(
        scenario["admin_token"]
    )

    statuses = scenario["statuses"]

    # --------------------------------------------------------
    # 1. SOLICITANTE CRIA O CHAMADO
    # --------------------------------------------------------

    response = client.post(
        "/tickets/",
        headers=requester_headers,
        json=ticket_payload(scenario),
    )

    assert response.status_code == 201, response.text

    created_ticket = response.json()

    ticket_id = created_ticket["id"]

    assert (
        created_ticket["requester_id"]
        == scenario["requester"].id
    )

    assert (
        created_ticket["status_id"]
        == statuses["Aberto"].id
    )

    assert created_ticket["assignee_id"] is None

    # --------------------------------------------------------
    # 2. ADMINISTRADOR ASSUME O CHAMADO
    # --------------------------------------------------------

    response = client.patch(
        f"/tickets/{ticket_id}",
        headers=admin_headers,
        json={
            "assignee_id": scenario["admin"].id,
        },
    )

    assert response.status_code == 200, response.text

    assert (
        response.json()["assignee_id"]
        == scenario["admin"].id
    )

    # --------------------------------------------------------
    # 3. INICIA O ATENDIMENTO
    # --------------------------------------------------------

    response = client.patch(
        f"/tickets/{ticket_id}/start",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text

    assert (
        response.json()["status_id"]
        == statuses["Em andamento"].id
    )

    # --------------------------------------------------------
    # 4. RESOLVE O CHAMADO
    # --------------------------------------------------------

    response = client.patch(
        f"/tickets/{ticket_id}/resolve",
        headers=admin_headers,
    )

    assert response.status_code == 200, response.text

    assert (
        response.json()["status_id"]
        == statuses["Resolvido"].id
    )

    # --------------------------------------------------------
    # 5. SOLICITANTE REABRE O CHAMADO
    # --------------------------------------------------------

    response = client.patch(
        f"/tickets/{ticket_id}/reopen",
        headers=requester_headers,
    )

    assert response.status_code == 200, response.text

    assert (
        response.json()["status_id"]
        == statuses["Reaberto"].id
    )

    # --------------------------------------------------------
    # 6. CONFERE O ESTADO FINAL
    # --------------------------------------------------------

    response = client.get(
        f"/tickets/{ticket_id}",
        headers=requester_headers,
    )

    assert response.status_code == 200, response.text

    assert (
        response.json()["status_id"]
        == statuses["Reaberto"].id
    )

    # --------------------------------------------------------
    # 7. CONFERE O HISTORICO
    # --------------------------------------------------------

    response = client.get(
        f"/tickets/{ticket_id}/history",
        headers=requester_headers,
    )

    assert response.status_code == 200, response.text

    actions = [
        entry["action"]
        for entry in response.json()
    ]

    expected_actions = [
        "created",
        "assigned",
        "started",
        "resolved",
        "reopened",
    ]

    for expected_action in expected_actions:
        assert expected_action in actions

    assert len(actions) >= 5


# ============================================================
# TESTE 2 - CHAMADO NAO PODE NASCER RESOLVIDO
# ============================================================

def test_ticket_cannot_be_created_as_resolved(
    client,
    ticket_scenario,
):

    scenario = ticket_scenario

    payload = ticket_payload(scenario)

    payload["status_id"] = scenario["statuses"]["Resolvido"].id

    response = client.post(
        "/tickets/",
        headers=auth_headers(
            scenario["requester_token"]
        ),
        json=payload,
    )

    assert response.status_code == 409, response.text


# ============================================================
# TESTE 3 - CHAMADO ABERTO NAO PODE SER RESOLVIDO DIRETAMENTE
# ============================================================

def test_ticket_cannot_be_resolved_before_start(
    client,
    ticket_scenario,
):

    scenario = ticket_scenario

    ticket_id = scenario["own_ticket"].id

    response = client.patch(
        f"/tickets/{ticket_id}/resolve",
        headers=auth_headers(
            scenario["admin_token"]
        ),
    )

    assert response.status_code == 409, response.text


# ============================================================
# TESTE 4 - SOLICITANTE NAO PODE ATRIBUIR RESPONSAVEL
# ============================================================

def test_requester_cannot_assign_ticket_during_creation(
    client,
    ticket_scenario,
):

    scenario = ticket_scenario

    payload = ticket_payload(scenario)

    payload["assignee_id"] = scenario["admin"].id

    response = client.post(
        "/tickets/",
        headers=auth_headers(
            scenario["requester_token"]
        ),
        json=payload,
    )

    assert response.status_code == 403, response.text


# ============================================================
# TESTE 5 - PATCH GENERICO NAO PODE ALTERAR STATUS
# ============================================================

def test_generic_update_cannot_change_ticket_status(
    client,
    ticket_scenario,
):

    scenario = ticket_scenario

    ticket_id = scenario["own_ticket"].id

    response = client.patch(
        f"/tickets/{ticket_id}",
        headers=auth_headers(
            scenario["admin_token"]
        ),
        json={
            "status_id": scenario["statuses"]["Resolvido"].id,
        },
    )

    assert response.status_code == 422, response.text