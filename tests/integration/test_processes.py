from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.permissions import PermissionNames
from app.core.security import create_access_token

from app.models.permission import Permission
from app.models.process import Process
from app.models.process_status import ProcessStatus
from app.models.process_type import ProcessType
from app.models.profile import Profile
from app.models.profile_permission import ProfilePermission
from app.models.sector import Sector
from app.models.user import User


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def process_scenario(db_session):

    unique = uuid4().hex

    sector = Sector(
        name=f"Processos teste {unique}",
        is_active=True,
    )

    admin_profile = Profile(
        name=f"Admin processos {unique}",
        is_active=True,
    )

    regular_profile = Profile(
        name=f"Usuario processos {unique}",
        is_active=True,
    )

    db_session.add_all([
        sector,
        admin_profile,
        regular_profile,
    ])
    db_session.flush()

    permission_names = [
        PermissionNames.PROCESSES_CREATE,
        PermissionNames.PROCESSES_READ,
        PermissionNames.PROCESSES_READ_ALL,
        PermissionNames.PROCESSES_UPDATE,
        PermissionNames.PROCESSES_UPDATE_ALL,
        PermissionNames.PROCESSES_ASSIGN,
    ]

    permissions = {}

    for name in permission_names:
        permission = Permission(
            name=name,
            is_active=True,
        )

        db_session.add(permission)
        permissions[name] = permission

    db_session.flush()

    for permission in permissions.values():
        db_session.add(
            ProfilePermission(
                profile_id=admin_profile.id,
                permission_id=permission.id,
                is_active=True,
            )
        )

    for name in [
        PermissionNames.PROCESSES_CREATE,
        PermissionNames.PROCESSES_READ,
        PermissionNames.PROCESSES_UPDATE,
    ]:
        db_session.add(
            ProfilePermission(
                profile_id=regular_profile.id,
                permission_id=permissions[name].id,
                is_active=True,
            )
        )

    admin = User(
        name="Admin Processos",
        email=f"admin-process-{unique}@example.test",
        password_hash="hash-de-teste",
        sector_id=sector.id,
        profile_id=admin_profile.id,
        is_active=True,
    )

    creator = User(
        name="Criador Processos",
        email=f"creator-process-{unique}@example.test",
        password_hash="hash-de-teste",
        sector_id=sector.id,
        profile_id=regular_profile.id,
        is_active=True,
    )

    other_user = User(
        name="Outro Usuario Processos",
        email=f"other-process-{unique}@example.test",
        password_hash="hash-de-teste",
        sector_id=sector.id,
        profile_id=regular_profile.id,
        is_active=True,
    )

    db_session.add_all([
        admin,
        creator,
        other_user,
    ])

    process_type = ProcessType(
        name=f"Tipo teste {unique}",
        is_active=True,
    )

    initial_status = ProcessStatus(
        name="Aberto",
        is_active=True,
    )

    db_session.add_all([
        process_type,
        initial_status,
    ])

    db_session.flush()

    process = Process(
        protocol=f"PRC-{uuid4().hex[:20].upper()}",
        title="Processo inicial de teste",
        description="Processo de integracao.",
        process_type_id=process_type.id,
        status_id=initial_status.id,
        created_by_id=creator.id,
        responsible_id=None,
    )

    db_session.add(process)
    db_session.flush()

    return {
        "admin": admin,
        "creator": creator,
        "other_user": other_user,
        "process": process,
        "process_type": process_type,
        "status": initial_status,
        "admin_token": create_access_token(str(admin.id)),
        "creator_token": create_access_token(str(creator.id)),
        "other_token": create_access_token(str(other_user.id)),
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