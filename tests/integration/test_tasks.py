
from datetime import datetime, timezone, timedelta

def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }

def tasks_url(process_id: int) -> str:
    return f"/processes/{process_id}/tasks"

def create_task(
    client,
    scenario,
    assigned_to_id=None,
):
    payload = {
        "title": "Conferir documentos",
        "description": "Conferir a documentacao do processo.",
    }

    if assigned_to_id is not None:
        payload["assigned_to_id"] = assigned_to_id

    response = client.post(
        tasks_url(scenario["process"].id),
        headers=headers(scenario["admin_token"]),
        json=payload,
    )

    assert response.status_code == 201, response.text

    return response.json()

# ============================================================
# 1. CRIAR TAREFA
# ============================================================

def test_admin_can_create_task(
    client,
    process_scenario,
):
    scenario = process_scenario

    task = create_task(client, scenario)

    assert task["title"] == "Conferir documentos"
    assert task["process_id"] == scenario["process"].id
    assert task["is_completed"] is False
    assert task["completed_at"] is None

# ============================================================
# 2. LISTAR TAREFAS
# ============================================================

def test_admin_can_list_process_tasks(
    client,
    process_scenario,
):
    scenario = process_scenario

    create_task(client, scenario)

    response = client.get(
        tasks_url(scenario["process"].id),
        headers=headers(scenario["admin_token"]),
    )

    assert response.status_code == 200, response.text
    assert len(response.json()) == 1

# ============================================================
# 3. CONSULTAR TAREFA
# ============================================================

def test_admin_can_get_task(
    client,
    process_scenario,
):
    scenario = process_scenario
    task = create_task(client, scenario)

    response = client.get(
        f'{tasks_url(scenario["process"].id)}/{task["id"]}',
        headers=headers(scenario["admin_token"]),
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == task["id"]

# ============================================================
# 4. ATUALIZAR TAREFA
# ============================================================

def test_admin_can_update_task(
    client,
    process_scenario,
):
    scenario = process_scenario
    task = create_task(client, scenario)

    response = client.patch(
        f'{tasks_url(scenario["process"].id)}/{task["id"]}',
        headers=headers(scenario["admin_token"]),
        json={
            "title": "Documentacao revisada",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["title"] == "Documentacao revisada"

# ============================================================
# 5. ATRIBUIR RESPONSAVEL
# ============================================================

def test_admin_can_assign_task(
    client,
    process_scenario,
):
    scenario = process_scenario

    task = create_task(
        client,
        scenario,
        assigned_to_id=scenario["creator"].id,
    )

    assert task["assigned_to_id"] == scenario["creator"].id

# ============================================================
# 6. USUARIO SEM PERMISSAO NAO PODE ATRIBUIR
# ============================================================

def test_creator_without_assign_permission_cannot_assign_task(
    client,
    process_scenario,
):
    scenario = process_scenario

    response = client.post(
        tasks_url(scenario["process"].id),
        headers=headers(scenario["creator_token"]),
        json={
            "title": "Tarefa sem autorizacao",
            "assigned_to_id": scenario["other_user"].id,
        },
    )

    assert response.status_code == 403, response.text

# ============================================================
# 7. CONCLUIR TAREFA
# ============================================================

def test_admin_can_complete_task(
    client,
    process_scenario,
):
    scenario = process_scenario
    task = create_task(client, scenario)

    response = client.post(
        f'{tasks_url(scenario["process"].id)}/{task["id"]}/complete',
        headers=headers(scenario["admin_token"]),
    )

    assert response.status_code == 200, response.text
    assert response.json()["is_completed"] is True
    assert response.json()["completed_at"] is not None

# ============================================================
# 8. IMPEDIR CONCLUSAO DUPLICADA
# ============================================================

def test_cannot_complete_task_twice(
    client,
    process_scenario,
):
    scenario = process_scenario
    task = create_task(client, scenario)

    url = (
        f'{tasks_url(scenario["process"].id)}/{task["id"]}/complete'
    )

    first = client.post(
        url,
        headers=headers(scenario["admin_token"]),
    )

    assert first.status_code == 200, first.text

    second = client.post(
        url,
        headers=headers(scenario["admin_token"]),
    )

    assert second.status_code == 409, second.text

# ============================================================
# 9. REABRIR TAREFA
# ============================================================

def test_admin_can_reopen_task(
    client,
    process_scenario,
):
    scenario = process_scenario
    task = create_task(client, scenario)

    base_url = (
        f'{tasks_url(scenario["process"].id)}/{task["id"]}'
    )

    completed = client.post(
        f"{base_url}/complete",
        headers=headers(scenario["admin_token"]),
    )

    assert completed.status_code == 200, completed.text

    response = client.post(
        f"{base_url}/reopen",
        headers=headers(scenario["admin_token"]),
    )

    assert response.status_code == 200, response.text
    assert response.json()["is_completed"] is False
    assert response.json()["completed_at"] is None

# ============================================================
# 10. IMPEDIR REABERTURA DE TAREFA ABERTA
# ============================================================

def test_cannot_reopen_task_that_is_not_completed(
    client,
    process_scenario,
):
    scenario = process_scenario
    task = create_task(client, scenario)

    response = client.post(
        f'{tasks_url(scenario["process"].id)}/{task["id"]}/reopen',
        headers=headers(scenario["admin_token"]),
    )

    assert response.status_code == 409, response.text

# ============================================================
# 11. IMPEDIR EDICAO DE TAREFA CONCLUIDA
# ============================================================

def test_cannot_update_completed_task(
    client,
    process_scenario,
):
    scenario = process_scenario
    task = create_task(client, scenario)

    url = (
        f'{tasks_url(scenario["process"].id)}/{task["id"]}'
    )

    completed = client.post(
        f"{url}/complete",
        headers=headers(scenario["admin_token"]),
    )

    assert completed.status_code == 200, completed.text

    response = client.patch(
        url,
        headers=headers(scenario["admin_token"]),
        json={
            "title": "Tentativa de alteracao",
        },
    )

    assert response.status_code == 422, response.text

# ============================================================
# 12. USUARIO SEM ACESSO NAO CONSULTA TAREFAS
# ============================================================

def test_unrelated_user_cannot_list_tasks(
    client,
    process_scenario,
):
    scenario = process_scenario

    response = client.get(
        tasks_url(scenario["process"].id),
        headers=headers(scenario["other_token"]),
    )

    assert response.status_code == 404, response.text