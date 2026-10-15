from uuid import uuid4

import pytest

from app.core.permissions import PermissionNames
from app.core.security import create_access_token

from app.models.user import User
from app.models.sector import Sector
from app.models.profile import Profile
from app.models.permission import Permission
from app.models.profile_permission import ProfilePermission

from app.models.ticket import Ticket
from app.models.ticket_status import TicketStatus
from app.models.ticket_priority import TicketPriority
from app.models.ticket_category import TicketCategory


@pytest.fixture
def ticket_scenario(db_session):
    """
    Prepara usuarios, perfis, permissoes e chamados
    exclusivamente na transacao do teste.
    """

    unique = uuid4().hex

    # 1. Criar setor

    sector = Sector(
        name=f"Setor teste {unique}",
        description="Setor criado pelos testes automatizados.",
        is_active=True,
    )

    db_session.add(sector)
    db_session.flush()

    # 2. Criar perfis

    admin_profile = Profile(
        name=f"Administrador teste {unique}",
        is_active=True,
    )

    requester_profile = Profile(
        name=f"Solicitante teste {unique}",
        is_active=True,
    )

    db_session.add_all([
        admin_profile,
        requester_profile,
    ])

    db_session.flush()

    # 3. Criar as permissoes necessarias

    permission_names = [
        PermissionNames.TICKETS_READ,
        PermissionNames.TICKETS_READ_ALL,
        PermissionNames.TICKETS_UPDATE,
        PermissionNames.TICKETS_UPDATE_ALL,
        PermissionNames.TICKETS_RESOLVE,
    ]

    permissions = {}

    for name in permission_names:

        permission = Permission(
            name=name,
            description="Permissao utilizada nos testes.",
            is_active=True,
        )

        db_session.add(permission)
        db_session.flush()

        permissions[name] = permission

    # 4. Permissoes do administrador

    for permission in permissions.values():

        db_session.add(
            ProfilePermission(
                profile_id=admin_profile.id,
                permission_id=permission.id,
                is_active=True,
            )
        )

    # 5. Permissoes do solicitante

    for name in [
        PermissionNames.TICKETS_READ,
        PermissionNames.TICKETS_UPDATE,
    ]:

        db_session.add(
            ProfilePermission(
                profile_id=requester_profile.id,
                permission_id=permissions[name].id,
                is_active=True,
            )
        )

    db_session.flush()

    # 6. Criar usuarios

    admin = User(
        name="Administrador Teste",
        email=f"admin-{unique}@example.test",
        password_hash="hash-nao-utilizado-neste-teste",
        sector_id=sector.id,
        profile_id=admin_profile.id,
        is_active=True,
    )

    requester = User(
        name="Solicitante Teste",
        email=f"requester-{unique}@example.test",
        password_hash="hash-nao-utilizado-neste-teste",
        sector_id=sector.id,
        profile_id=requester_profile.id,
        is_active=True,
    )

    other_user = User(
        name="Outro Solicitante",
        email=f"other-{unique}@example.test",
        password_hash="hash-nao-utilizado-neste-teste",
        sector_id=sector.id,
        profile_id=requester_profile.id,
        is_active=True,
    )

    db_session.add_all([
        admin,
        requester,
        other_user,
    ])

    db_session.flush()

    # 7. Criar classificacoes dos chamados

    ticket_status = TicketStatus(
        name="Aberto",
        description="Status inicial dos chamados.",
        is_active=True,
    )

    ticket_priority = TicketPriority(
        name="Media",
        description="Prioridade de teste.",
        is_active=True,
    )

    ticket_category = TicketCategory(
        name="Sistema",
        description="Categoria de teste.",
        is_active=True,
    )

    db_session.add_all([
        ticket_status,
        ticket_priority,
        ticket_category,
    ])

    db_session.flush()

    # 8. Criar chamados pertencentes a usuarios diferentes

    own_ticket = Ticket(
        title="Chamado do solicitante",
        description="Chamado criado pelo teste de integracao.",
        status_id=ticket_status.id,
        priority_id=ticket_priority.id,
        category_id=ticket_category.id,
        requester_id=requester.id,
        assignee_id=None,
    )

    other_ticket = Ticket(
        title="Chamado de outra pessoa",
        description="Chamado utilizado para verificar acesso negado.",
        status_id=ticket_status.id,
        priority_id=ticket_priority.id,
        category_id=ticket_category.id,
        requester_id=other_user.id,
        assignee_id=None,
    )

    db_session.add_all([
        own_ticket,
        other_ticket,
    ])

    db_session.flush()

    # 9. Gerar tokens reais do projeto

    admin_token = create_access_token(
        subject=str(admin.id)
    )

    requester_token = create_access_token(
        subject=str(requester.id)
    )

    other_token = create_access_token(
        subject=str(other_user.id)
    )

    return {
        "admin": admin,
        "requester": requester,
        "other_user": other_user,
        "own_ticket": own_ticket,
        "other_ticket": other_ticket,
        "admin_token": admin_token,
        "requester_token": requester_token,
        "other_token": other_token,
    }


def auth_headers(token: str) -> dict:
    """
    Monta o cabecalho de autenticacao HTTP.
    """

    return {
        "Authorization": f"Bearer {token}"
    }


# TESTE 1: solicitante consulta o proprio chamado

def test_requester_can_read_own_ticket(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["own_ticket"]
    token = ticket_scenario["requester_token"]

    response = client.get(
        f"/tickets/{ticket.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == ticket.id


# TESTE 2: solicitante nao consulta chamado alheio

def test_requester_cannot_read_another_ticket(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["other_ticket"]
    token = ticket_scenario["requester_token"]

    response = client.get(
        f"/tickets/{ticket.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


# TESTE 3: administrador consulta chamado de outra pessoa

def test_admin_can_read_any_ticket(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["other_ticket"]
    token = ticket_scenario["admin_token"]

    response = client.get(
        f"/tickets/{ticket.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == ticket.id


# TESTE 4: usuario nao pode editar chamado que nao lhe foi atribuido

def test_requester_cannot_edit_unassigned_ticket(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["own_ticket"]
    token = ticket_scenario["requester_token"]

    response = client.patch(
        f"/tickets/{ticket.id}",
        headers=auth_headers(token),
        json={
            "title": "Alteracao nao autorizada"
        },
    )

    assert response.status_code == 403


# TESTE 5: usuario sem tickets.comment nao pode comentar

def test_user_without_comment_permission_cannot_comment(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["own_ticket"]
    token = ticket_scenario["requester_token"]

    response = client.post(
        f"/tickets/{ticket.id}/comments",
        headers=auth_headers(token),
        json={
            "content": "Comentario de teste."
        },
    )

    assert response.status_code == 403


# TESTE 6: transicao invalida retorna 409

def test_invalid_ticket_transition_returns_409(
    client,
    ticket_scenario,
):

    ticket = ticket_scenario["own_ticket"]
    token = ticket_scenario["admin_token"]

    # O chamado esta Aberto, mas a resolucao exige
    # que esteja Em andamento.

    response = client.patch(
        f"/tickets/{ticket.id}/resolve",
        headers=auth_headers(token),
    )

    assert response.status_code == 409


# TESTE 7: listagem respeita o acesso individual

def test_requester_lists_only_related_tickets(
    client,
    ticket_scenario,
):

    token = ticket_scenario["requester_token"]

    response = client.get(
        "/tickets/",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        ticket["id"]
        for ticket in response.json()
    }

    assert ticket_scenario["own_ticket"].id in returned_ids

    assert ticket_scenario["other_ticket"].id not in returned_ids