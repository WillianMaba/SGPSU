import pytest

from app.core.permissions import PermissionNames
from app.models.permission import Permission
from app.models.profile_permission import ProfilePermission


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