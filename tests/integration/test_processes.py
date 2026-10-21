def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }




def test_creator_can_create_process(
    client,
    process_scenario,
):

    scenario = process_scenario

    response = client.post(
        "/processes/",
        headers=headers(scenario["creator_token"]),
        json={
            "title": "Novo processo administrativo",
            "description": "Processo aberto pela API.",
            "process_type_id": scenario["process_type"].id,
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["protocol"].startswith("PRC-")
    assert data["created_by_id"] == scenario["creator"].id
    assert data["status_id"] == scenario["status"].id
    assert data["responsible_id"] is None


def test_creator_can_read_own_process(
    client,
    process_scenario,
):

    scenario = process_scenario

    response = client.get(
        f'/processes/{scenario["process"].id}',
        headers=headers(scenario["creator_token"]),
    )

    assert response.status_code == 200, response.text


def test_other_user_cannot_read_process(
    client,
    process_scenario,
):

    scenario = process_scenario

    response = client.get(
        f'/processes/{scenario["process"].id}',
        headers=headers(scenario["other_token"]),
    )

    assert response.status_code == 404, response.text


def test_admin_can_read_any_process(
    client,
    process_scenario,
):

    scenario = process_scenario

    response = client.get(
        f'/processes/{scenario["process"].id}',
        headers=headers(scenario["admin_token"]),
    )

    assert response.status_code == 200, response.text


def test_creator_cannot_assign_without_permission(
    client,
    process_scenario,
):

    scenario = process_scenario

    response = client.patch(
        f'/processes/{scenario["process"].id}',
        headers=headers(scenario["creator_token"]),
        json={
            "responsible_id": scenario["other_user"].id,
        },
    )

    # O criador nao e responsavel e nao possui update_all.
    assert response.status_code == 403, response.text


def test_admin_can_assign_responsible(
    client,
    process_scenario,
):

    scenario = process_scenario

    response = client.patch(
        f'/processes/{scenario["process"].id}',
        headers=headers(scenario["admin_token"]),
        json={
            "responsible_id": scenario["other_user"].id,
        },
    )

    assert response.status_code == 200, response.text

    assert (
        response.json()["responsible_id"]
        == scenario["other_user"].id
    )


def test_generic_patch_cannot_change_status(
    client,
    process_scenario,
):

    scenario = process_scenario

    response = client.patch(
        f'/processes/{scenario["process"].id}',
        headers=headers(scenario["admin_token"]),
        json={
            "status_id": scenario["status"].id,
        },
    )

    assert response.status_code == 422, response.text


def test_user_list_contains_only_related_processes(
    client,
    process_scenario,
):

    scenario = process_scenario

    response = client.get(
        "/processes/",
        headers=headers(scenario["other_token"]),
    )

    assert response.status_code == 200, response.text

    process_ids = {
        item["id"]
        for item in response.json()
    }

    assert scenario["process"].id not in process_ids