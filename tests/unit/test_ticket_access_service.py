from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from app.services import ticket_access_service as access_module
from app.services.ticket_access_service import TicketAccessService


@pytest.fixture
def access_factory(monkeypatch):
    """
    Cria um TicketAccessService com a consulta de permissoes simulada.
    Nao conecta ao PostgreSQL.
    """

    def factory(permissions=None):
        permissions = set(permissions or [])

        authorization = Mock()

        authorization.has_permission.side_effect = (
            lambda user, permission_name: permission_name in permissions
        )

        monkeypatch.setattr(
            access_module,
            "AuthorizationService",
            lambda db: authorization,
        )

        db = Mock()
        service = TicketAccessService(db)

        return service

    return factory


@pytest.fixture
def user():
    return SimpleNamespace(
        id=10,
        profile_id=2,
        is_active=True,
    )


@pytest.fixture
def own_ticket():
    return SimpleNamespace(
        id=100,
        requester_id=10,
        assignee_id=None,
    )


@pytest.fixture
def other_ticket():
    return SimpleNamespace(
        id=200,
        requester_id=20,
        assignee_id=30,
    )


def test_requester_can_read_own_ticket(
    access_factory,
    user,
    own_ticket,
):
    service = access_factory({"tickets.read"})

    assert service.can_read(user, own_ticket) is True


def test_assignee_can_read_assigned_ticket(
    access_factory,
    user,
    other_ticket,
):
    other_ticket.assignee_id = user.id

    service = access_factory({"tickets.read"})

    assert service.can_read(user, other_ticket) is True


def test_user_cannot_read_another_ticket(
    access_factory,
    user,
    other_ticket,
):
    service = access_factory({"tickets.read"})

    assert service.can_read(user, other_ticket) is False


def test_requester_without_read_permission_is_denied(
    access_factory,
    user,
    own_ticket,
):
    service = access_factory()

    assert service.can_read(user, own_ticket) is False


def test_read_all_allows_reading_another_ticket(
    access_factory,
    user,
    other_ticket,
):
    service = access_factory({"tickets.read_all"})

    assert service.can_read(user, other_ticket) is True


def test_assignee_with_update_permission_can_edit(
    access_factory,
    user,
    other_ticket,
):
    other_ticket.assignee_id = user.id

    service = access_factory({"tickets.update"})

    assert service.can_update(user, other_ticket) is True


def test_requester_without_assignment_cannot_edit(
    access_factory,
    user,
    own_ticket,
):
    service = access_factory({"tickets.update"})

    assert service.can_update(user, own_ticket) is False


def test_update_all_allows_editing_another_ticket(
    access_factory,
    user,
    other_ticket,
):
    service = access_factory({"tickets.update_all"})

    assert service.can_update(user, other_ticket) is True


def test_require_read_denies_unauthorized_access(
    access_factory,
    user,
    other_ticket,
):
    service = access_factory({"tickets.read"})

    with pytest.raises(HTTPException) as error:
        service.require_read(user, other_ticket)

    assert error.value.status_code == 404


def test_require_update_denies_unauthorized_access(
    access_factory,
    user,
    other_ticket,
):
    service = access_factory({"tickets.update"})

    with pytest.raises(HTTPException) as error:
        service.require_update(user, other_ticket)

    assert error.value.status_code == 403