from importlib import import_module

import pytest

from app.core import storage


attachment_routes = import_module(
    "app.api.routes.ticket_attachments"
)


def auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def temporary_ticket_storage(
    tmp_path,
    monkeypatch,
):
    """
    Redireciona os anexos para uma pasta temporaria.

    A pasta sera removida pelo mecanismo tmp_path do pytest,
    sem interferir no armazenamento normal do SGPSU.
    """

    project_root = tmp_path

    storage_dir = (
        project_root / "storage" / "tickets"
    )

    storage_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Variaveis consultadas pela funcao que resolve caminhos.
    monkeypatch.setattr(
        storage,
        "PROJECT_ROOT",
        project_root,
    )

    monkeypatch.setattr(
        storage,
        "TICKET_STORAGE_DIR",
        storage_dir,
    )

    # A rota importou essa constante diretamente.
    # Portanto, precisamos atualizar sua referencia tambem.
    monkeypatch.setattr(
        attachment_routes,
        "TICKET_STORAGE_DIR",
        storage_dir,
    )

    yield storage_dir


def test_upload_and_download_attachment(
    client,
    ticket_scenario,
    temporary_ticket_storage,
):
    scenario = ticket_scenario
    ticket = scenario["own_ticket"]

    contents = b"Arquivo de teste do SGPSU."

    # 1. Envia o arquivo.
    response = client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_headers(scenario["admin_token"]),
        files={
            "upload": (
                "teste.txt",
                contents,
                "text/plain",
            ),
        },
    )

    assert response.status_code == 201, response.text

    attachment = response.json()

    assert attachment["ticket_id"] == ticket.id
    assert attachment["original_filename"] == "teste.txt"
    assert attachment["file_size"] == len(contents)

    attachment_id = attachment["id"]

    # 2. Confirma que o arquivo foi criado na pasta temporaria.
    stored_files = list(
        temporary_ticket_storage.iterdir()
    )

    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == contents

    # 3. Faz o download pelo endpoint.
    download = client.get(
        f"/tickets/{ticket.id}/attachments/{attachment_id}",
        headers=auth_headers(scenario["admin_token"]),
    )

    assert download.status_code == 200, download.text
    assert download.content == contents


def test_attachment_appears_in_list_and_history(
    client,
    ticket_scenario,
    temporary_ticket_storage,
):
    scenario = ticket_scenario
    ticket = scenario["own_ticket"]

    response = client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_headers(scenario["admin_token"]),
        files={
            "upload": (
                "relatorio.txt",
                b"Conteudo do relatorio.",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 201, response.text

    attachment_id = response.json()["id"]

    # Consulta a lista de anexos.
    listing = client.get(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_headers(scenario["requester_token"]),
    )

    assert listing.status_code == 200, listing.text

    returned_ids = {
        item["id"]
        for item in listing.json()
    }

    assert attachment_id in returned_ids

    # Confirma o registro no historico.
    history = client.get(
        f"/tickets/{ticket.id}/history",
        headers=auth_headers(scenario["admin_token"]),
    )

    assert history.status_code == 200, history.text

    actions = [
        entry["action"]
        for entry in history.json()
    ]

    assert "attachment_added" in actions


def test_user_cannot_download_attachment_from_another_ticket(
    client,
    ticket_scenario,
    temporary_ticket_storage,
):
    scenario = ticket_scenario
    ticket = scenario["other_ticket"]

    # O administrador adiciona um anexo ao chamado alheio.
    created = client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_headers(scenario["admin_token"]),
        files={
            "upload": (
                "privado.txt",
                b"Informacao de teste.",
                "text/plain",
            ),
        },
    )

    assert created.status_code == 201, created.text

    attachment_id = created.json()["id"]

    # O solicitante de outro chamado tenta baixar o arquivo.
    response = client.get(
        f"/tickets/{ticket.id}/attachments/{attachment_id}",
        headers=auth_headers(scenario["requester_token"]),
    )

    assert response.status_code == 404, response.text


def test_upload_rejects_file_larger_than_10_mb(
    client,
    ticket_scenario,
    temporary_ticket_storage,
):
    scenario = ticket_scenario
    ticket = scenario["own_ticket"]

    oversized_content = b"x" * (
        storage.MAX_TICKET_ATTACHMENT_SIZE + 1
    )

    response = client.post(
        f"/tickets/{ticket.id}/attachments",
        headers=auth_headers(scenario["admin_token"]),
        files={
            "upload": (
                "grande.txt",
                oversized_content,
                "text/plain",
            ),
        },
    )

    assert response.status_code == 413, response.text

    # Nenhum arquivo deve ter sido salvo.
    assert list(temporary_ticket_storage.iterdir()) == []