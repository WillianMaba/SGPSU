
def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }


def stages_url(process_id: int) -> str:
    return f"/processes/{process_id}/stages"


def create_stage(
    client,
    scenario,
    sequence: int = 1,
):
    response = client.post(
        stages_url(scenario["process"].id),
        headers=headers(scenario["admin_token"]),
        json={
            "name": f"Etapa {sequence}",
            "description": "Etapa de teste.",
            "sequence": sequence,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


# ============================================================
# 1. CRIAR ETAPA
# ============================================================

def test_admin_can_create_stage(
    client,
    process_scenario,
):
    scenario = process_scenario

    stage = create_stage(client, scenario)

    assert stage["name"] == "Etapa 1"
    assert stage["sequence"] == 1
    assert stage["process_id"] == scenario["process"].id
    assert stage["is_completed"] is False
    assert stage["started_at"] is None


# ============================================================
# 2. IMPEDIR SEQUENCIA DUPLICADA
# ============================================================

def test_duplicate_sequence_returns_409(
    client,
    process_scenario,
):
    scenario = process_scenario

    create_stage(client, scenario, sequence=1)

    response = client.post(
        stages_url(scenario["process"].id),
        headers=headers(scenario["admin_token"]),
        json={
            "name": "Outra etapa",
            "sequence": 1,
        },
    )

    assert response.status_code == 409, response.text


# ============================================================
# 3. LISTAR ETAPAS EM ORDEM
# ============================================================

def test_stages_are_listed_in_sequence_order(
    client,
    process_scenario,
):
    scenario = process_scenario

    create_stage(client, scenario, sequence=3)
    create_stage(client, scenario, sequence=1)
    create_stage(client, scenario, sequence=2)

    response = client.get(
        stages_url(scenario["process"].id),
        headers=headers(scenario["creator_token"]),
    )

    assert response.status_code == 200, response.text

    sequences = [
        item["sequence"]
        for item in response.json()
    ]

    assert sequences == [1, 2, 3]


# ============================================================
# 4. ATUALIZAR ETAPA
# ============================================================

def test_admin_can_update_stage(
    client,
    process_scenario,
):
    scenario = process_scenario
    stage = create_stage(client, scenario)

    response = client.patch(
        f'{stages_url(scenario["process"].id)}/{stage["id"]}',
        headers=headers(scenario["admin_token"]),
        json={
            "name": "Analise documental",
            "description": "Documentos em revisao.",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Analise documental"


# ============================================================
# 5. INICIAR ETAPA
# ============================================================

def test_admin_can_start_stage(
    client,
    process_scenario,
):
    scenario = process_scenario
    stage = create_stage(client, scenario)

    response = client.post(
        f'{stages_url(scenario["process"].id)}/{stage["id"]}/start',
        headers=headers(scenario["admin_token"]),
    )

    assert response.status_code == 200, response.text
    assert response.json()["started_at"] is not None
    assert response.json()["is_completed"] is False


# ============================================================
# 6. IMPEDIR CONCLUSAO ANTES DO INICIO
# ============================================================

def test_cannot_complete_stage_before_start(
    client,
    process_scenario,
):
    scenario = process_scenario
    stage = create_stage(client, scenario)

    response = client.post(
        f'{stages_url(scenario["process"].id)}/{stage["id"]}/complete',
        headers=headers(scenario["admin_token"]),
    )

    assert response.status_code == 409, response.text


# ============================================================
# 7. CONCLUIR ETAPA INICIADA
# ============================================================

def test_admin_can_complete_started_stage(
    client,
    process_scenario,
):
    scenario = process_scenario
    stage = create_stage(client, scenario)

    url = (
        f'{stages_url(scenario["process"].id)}/{stage["id"]}'
    )

    start_response = client.post(
        f"{url}/start",
        headers=headers(scenario["admin_token"]),
    )

    assert start_response.status_code == 200, start_response.text

    response = client.post(
        f"{url}/complete",
        headers=headers(scenario["admin_token"]),
    )

    assert response.status_code == 200, response.text
    assert response.json()["is_completed"] is True
    assert response.json()["completed_at"] is not None


# ============================================================
# 8. HISTORICO DAS ALTERACOES
# ============================================================

def test_stage_history_records_actions(
    client,
    process_scenario,
):
    scenario = process_scenario
    stage = create_stage(client, scenario)

    url = (
        f'{stages_url(scenario["process"].id)}/{stage["id"]}'
    )

    response = client.post(
        f"{url}/start",
        headers=headers(scenario["admin_token"]),
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"{url}/complete",
        headers=headers(scenario["admin_token"]),
    )
    assert response.status_code == 200, response.text

    response = client.get(
        f"{url}/history",
        headers=headers(scenario["creator_token"]),
    )

    assert response.status_code == 200, response.text

    actions = [
        item["action"]
        for item in response.json()
    ]

    assert actions == [
        "created",
        "started",
        "completed",
    ]

    assert all(
        item["user_id"] == scenario["admin"].id
        for item in response.json()
    )


# ============================================================
# 9. USUARIO SEM ACESSO NAO CONSULTA ETAPAS
# ============================================================

def test_unrelated_user_cannot_read_stages(
    client,
    process_scenario,
):
    scenario = process_scenario

    response = client.get(
        stages_url(scenario["process"].id),
        headers=headers(scenario["other_token"]),
    )

    assert response.status_code == 404, response.text


# ============================================================
# 10. CRIADOR SEM PERMISSAO DE EDICAO NAO CRIA ETAPAS
# ============================================================

def test_creator_without_update_access_cannot_create_stage(
    client,
    process_scenario,
):
    scenario = process_scenario

    response = client.post(
        stages_url(scenario["process"].id),
        headers=headers(scenario["creator_token"]),
        json={
            "name": "Etapa nao autorizada",
            "sequence": 1,
        },
    )

    assert response.status_code == 403, response.text
