from app.models.process_progress import ProcessProgress


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }


def progress_url(process_id: int) -> str:
    return f"/processes/{process_id}/progress"


# ============================================================
# 1. ADMINISTRADOR REGISTRA MOVIMENTACAO
# ============================================================

def test_admin_can_add_process_progress(
    client,
    process_scenario,
):
    scenario = process_scenario

    response = client.post(
        progress_url(scenario["process"].id),
        headers=headers(scenario["admin_token"]),
        json={
            "description": "Documentacao recebida para analise."
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["process_id"] == scenario["process"].id
    assert data["user_id"] == scenario["admin"].id
    assert data["description"] == "Documentacao recebida para analise."
    assert data["id"] > 0
    assert data["created_at"] is not None


# ============================================================
# 2. CONSULTA DAS MOVIMENTACOES EM ORDEM CRONOLOGICA
# ============================================================

def test_admin_can_list_process_progress_in_order(
    client,
    process_scenario,
):
    scenario = process_scenario
    url = progress_url(scenario["process"].id)
    auth = headers(scenario["admin_token"])

    descriptions = [
        "Primeira movimentacao.",
        "Segunda movimentacao.",
        "Terceira movimentacao.",
    ]

    for description in descriptions:
        response = client.post(
            url,
            headers=auth,
            json={"description": description},
        )

        assert response.status_code == 201, response.text

    response = client.get(
        url,
        headers=auth,
    )

    assert response.status_code == 200, response.text

    returned_descriptions = [
        item["description"]
        for item in response.json()
    ]

    assert returned_descriptions == descriptions


# ============================================================
# 3. DESCRICAO CONTENDO APENAS ESPACOS
# ============================================================

def test_progress_rejects_blank_description(
    client,
    process_scenario,
):
    scenario = process_scenario

    response = client.post(
        progress_url(scenario["process"].id),
        headers=headers(scenario["admin_token"]),
        json={
            "description": "     "
        },
    )

    assert response.status_code == 422, response.text


# ============================================================
# 4. USUARIO SEM ACESSO NAO CONSULTA MOVIMENTACOES
# ============================================================

def test_unrelated_user_cannot_read_process_progress(
    client,
    process_scenario,
):
    scenario = process_scenario

    response = client.get(
        progress_url(scenario["process"].id),
        headers=headers(scenario["other_token"]),
    )

    assert response.status_code == 404, response.text


# ============================================================
# 5. CRIADOR SEM AUTORIZACAO DE EDICAO NAO MOVIMENTA
# ============================================================

def test_creator_without_update_access_cannot_add_progress(
    client,
    process_scenario,
):
    scenario = process_scenario

    response = client.post(
        progress_url(scenario["process"].id),
        headers=headers(scenario["creator_token"]),
        json={
            "description": "Tentativa de movimentacao."
        },
    )

    assert response.status_code == 403, response.text


# ============================================================
# 6. CRIADOR CONSEGUE CONSULTAR MOVIMENTACOES
# ============================================================

def test_creator_can_read_process_progress(
    client,
    process_scenario,
):
    scenario = process_scenario
    url = progress_url(scenario["process"].id)

    creation_response = client.post(
        url,
        headers=headers(scenario["admin_token"]),
        json={
            "description": "Movimentacao registrada pelo administrador."
        },
    )

    assert creation_response.status_code == 201, creation_response.text

    response = client.get(
        url,
        headers=headers(scenario["creator_token"]),
    )

    assert response.status_code == 200, response.text

    descriptions = [
        item["description"]
        for item in response.json()
    ]

    assert "Movimentacao registrada pelo administrador." in descriptions


# ============================================================
# 7. AUTOR DA MOVIMENTACAO VEM DO JWT
# ============================================================

def test_progress_author_is_authenticated_user(
    client,
    process_scenario,
    db_session,
):
    scenario = process_scenario

    response = client.post(
        progress_url(scenario["process"].id),
        headers=headers(scenario["admin_token"]),
        json={
            "description": "Registro com autor autenticado.",
        },
    )

    assert response.status_code == 201, response.text

    progress_id = response.json()["id"]

    saved_progress = db_session.get(
        ProcessProgress,
        progress_id,
    )

    assert saved_progress is not None

    assert saved_progress.user_id == scenario["admin"].id
    assert saved_progress.process_id == scenario["process"].id
    assert (
        saved_progress.description
        == "Registro com autor autenticado."
    )