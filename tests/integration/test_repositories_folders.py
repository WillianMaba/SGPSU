import pytest

from app.core.permissions import PermissionNames
from app.models.permission import Permission
from app.models.profile_permission import ProfilePermission
from app.models.repository_access import RepositoryAccess


@pytest.fixture
def repository_scenario(db_session, process_scenario):
    names = [
        PermissionNames.REPOSITORIES_CREATE,
        PermissionNames.REPOSITORIES_READ,
        PermissionNames.REPOSITORIES_UPDATE,
        PermissionNames.FOLDERS_CREATE,
        PermissionNames.FOLDERS_READ,
        PermissionNames.FOLDERS_UPDATE,
    ]

    permissions = {}

    for name in names:
        permission = Permission(
            name=name,
            description="Permissao utilizada nos testes de repositorios.",
            is_active=True,
        )
        db_session.add(permission)
        permissions[name] = permission

    db_session.flush()

    # Administrador recebe todas as permissões do módulo.
    for permission in permissions.values():
        db_session.add(
            ProfilePermission(
                profile_id=process_scenario["admin"].profile_id,
                permission_id=permission.id,
                is_active=True,
            )
        )

    # Usuário comum recebe permissões funcionais,
    # mas só acessará recursos autorizados pela ACL.
    for name in [
        PermissionNames.REPOSITORIES_CREATE,
        PermissionNames.REPOSITORIES_READ,
        PermissionNames.FOLDERS_CREATE,
        PermissionNames.FOLDERS_READ,
        PermissionNames.FOLDERS_UPDATE,
    ]:
        db_session.add(
            ProfilePermission(
                profile_id=process_scenario["creator"].profile_id,
                permission_id=permissions[name].id,
                is_active=True,
            )
        )

    db_session.flush()

    return process_scenario


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_repository(client, token: str, name: str = "Repositorio teste"):
    response = client.post(
        "/repositories/",
        headers=auth(token),
        json={
            "name": name,
            "description": "Repositorio criado pelo teste.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_creator_can_create_and_access_repository(
    client,
    repository_scenario,
):
    token = repository_scenario["creator_token"]

    repository = create_repository(client, token)

    response = client.get(
        f"/repositories/{repository['id']}",
        headers=auth(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == repository["id"]


def test_other_user_cannot_list_repository_without_acl(
    client,
    repository_scenario,
):
    creator_token = repository_scenario["creator_token"]
    other_token = repository_scenario["other_token"]

    create_repository(client, creator_token)

    response = client.get(
        "/repositories/",
        headers=auth(other_token),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_create_root_and_child_folders(
    client,
    repository_scenario,
):
    token = repository_scenario["creator_token"]
    repository = create_repository(client, token)

    root_response = client.post(
        f"/repositories/{repository['id']}/folders",
        headers=auth(token),
        json={
            "name": "Documentos",
            "description": "Pasta raiz.",
        },
    )

    assert root_response.status_code == 201, root_response.text
    root = root_response.json()

    child_response = client.post(
        f"/repositories/{repository['id']}/folders",
        headers=auth(token),
        json={
            "name": "Contratos",
            "parent_folder_id": root["id"],
        },
    )

    assert child_response.status_code == 201, child_response.text
    child = child_response.json()

    assert child["repository_id"] == repository["id"]
    assert child["parent_folder_id"] == root["id"]


def test_folder_cannot_use_parent_from_another_repository(
    client,
    repository_scenario,
):
    token = repository_scenario["creator_token"]

    first = create_repository(client, token, "Repositorio um")
    second = create_repository(client, token, "Repositorio dois")

    root_response = client.post(
        f"/repositories/{first['id']}/folders",
        headers=auth(token),
        json={"name": "Pasta original"},
    )
    assert root_response.status_code == 201, root_response.text

    response = client.post(
        f"/repositories/{second['id']}/folders",
        headers=auth(token),
        json={
            "name": "Pasta invalida",
            "parent_folder_id": root_response.json()["id"],
        },
    )

    assert response.status_code == 404


def test_folder_cannot_be_moved_inside_its_descendant(
    client,
    repository_scenario,
):
    token = repository_scenario["creator_token"]
    repository = create_repository(client, token)

    root_response = client.post(
        f"/repositories/{repository['id']}/folders",
        headers=auth(token),
        json={"name": "Raiz"},
    )
    assert root_response.status_code == 201, root_response.text
    root = root_response.json()

    child_response = client.post(
        f"/repositories/{repository['id']}/folders",
        headers=auth(token),
        json={
            "name": "Filha",
            "parent_folder_id": root["id"],
        },
    )
    assert child_response.status_code == 201, child_response.text
    child = child_response.json()

    response = client.patch(
        f"/repositories/{repository['id']}/folders/{root['id']}",
        headers=auth(token),
        json={"parent_folder_id": child["id"]},
    )

    assert response.status_code == 422

def test_creator_can_list_root_and_child_folders(
    client,
    repository_scenario,
):
    token = repository_scenario["creator_token"]
    repository = create_repository(client, token)

    root_response = client.post(
        f"/repositories/{repository['id']}/folders",
        headers=auth(token),
        json={"name": "Documentos"},
    )
    assert root_response.status_code == 201, root_response.text
    root = root_response.json()

    child_response = client.post(
        f"/repositories/{repository['id']}/folders",
        headers=auth(token),
        json={
            "name": "Contratos",
            "parent_folder_id": root["id"],
        },
    )
    assert child_response.status_code == 201, child_response.text

    root_list = client.get(
        f"/repositories/{repository['id']}/folders",
        headers=auth(token),
    )

    assert root_list.status_code == 200
    assert [folder["id"] for folder in root_list.json()] == [root["id"]]

    child_list = client.get(
        f"/repositories/{repository['id']}/folders",
        params={"parent_folder_id": root["id"]},
        headers=auth(token),
    )

    assert child_list.status_code == 200
    assert len(child_list.json()) == 1
    assert child_list.json()[0]["name"] == "Contratos"


def test_creator_can_update_folder(
    client,
    repository_scenario,
):
    token = repository_scenario["creator_token"]
    repository = create_repository(client, token)

    folder_response = client.post(
        f"/repositories/{repository['id']}/folders",
        headers=auth(token),
        json={"name": "Nome original"},
    )
    assert folder_response.status_code == 201, folder_response.text

    folder_id = folder_response.json()["id"]

    response = client.patch(
        f"/repositories/{repository['id']}/folders/{folder_id}",
        headers=auth(token),
        json={"name": "Nome atualizado"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Nome atualizado"


def test_explicit_deny_blocks_repository_read(
    client,
    db_session,
    repository_scenario,
):
    creator_token = repository_scenario["creator_token"]
    other_user = repository_scenario["other_user"]

    repository = create_repository(client, creator_token)

    db_session.add(
        RepositoryAccess(
            repository_id=repository["id"],
            user_id=other_user.id,
            profile_id=None,
            sector_id=None,
            permission="READ",
            effect="DENY",
            is_active=True,
        )
    )
    db_session.flush()

    response = client.get(
        f"/repositories/{repository['id']}",
        headers=auth(repository_scenario["other_token"]),
    )

    assert response.status_code == 403


def test_other_user_cannot_read_folder_without_acl(
    client,
    repository_scenario,
):
    creator_token = repository_scenario["creator_token"]
    other_token = repository_scenario["other_token"]

    repository = create_repository(client, creator_token)

    folder_response = client.post(
        f"/repositories/{repository['id']}/folders",
        headers=auth(creator_token),
        json={"name": "Restrita"},
    )
    assert folder_response.status_code == 201, folder_response.text

    folder_id = folder_response.json()["id"]

    response = client.get(
        f"/repositories/{repository['id']}/folders/{folder_id}",
        headers=auth(other_token),
    )

    assert response.status_code == 403
