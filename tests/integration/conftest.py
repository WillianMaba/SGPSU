import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from tests.integration.database_guard import validate_test_database

from alembic.config import Config
from alembic.script import ScriptDirectory


# ============================================================
# PROTECAO DO AMBIENTE DE TESTES
# ============================================================

# Esta verificacao acontece antes de importar a aplicacao.

if os.getenv("SGPSU_ENV_FILE") != ".env.test":
    raise RuntimeError(
        "BLOQUEIO: os testes de integracao exigem "
        "SGPSU_ENV_FILE=.env.test."
    )


from app.core.config import settings  # noqa: E402

validate_test_database(settings.database_url)


# ============================================================
# IMPORTS DA APLICACAO
# ============================================================

from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

from app.core.permissions import PermissionNames  # noqa: E402
from app.core.security import create_access_token  # noqa: E402

from app.models.user import User  # noqa: E402
from app.models.sector import Sector  # noqa: E402
from app.models.profile import Profile  # noqa: E402
from app.models.permission import Permission  # noqa: E402
from app.models.profile_permission import ProfilePermission  # noqa: E402

from app.models.ticket import Ticket  # noqa: E402
from app.models.ticket_status import TicketStatus  # noqa: E402
from app.models.ticket_priority import TicketPriority  # noqa: E402
from app.models.ticket_category import TicketCategory  # noqa: E402


# ============================================================
# ENGINE EXCLUSIVO DOS TESTES
# ============================================================

@pytest.fixture(scope="session")
def test_engine():

    engine = create_engine(
        settings.database_url,
    )

    try:
        with engine.connect() as connection:

            database_name = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

            if database_name != "sgpsu_test":
                raise RuntimeError(
                    "BLOQUEIO: conexao realizada com o banco errado."
                )

            migration_table = connection.execute(
                text("SELECT to_regclass('public.alembic_version')")
            ).scalar_one()

            if migration_table is None:
                raise RuntimeError(
                    "O banco sgpsu_test ainda nao recebeu as migrations."
                )

            revision = connection.execute(
                text("SELECT version_num FROM public.alembic_version")
            ).scalar_one_or_none()

            alembic_config = Config("alembic.ini")
            script = ScriptDirectory.from_config(alembic_config)

            expected_revision = script.get_current_head()

            if revision != expected_revision:
                raise RuntimeError(
                    "O banco de testes nao esta atualizado. "
                    f"Esperado: {expected_revision}. Encontrado: {revision}"
    )    
                
            

        yield engine

    finally:
        engine.dispose()


# ============================================================
# SESSAO ISOLADA POR TESTE
# ============================================================

@pytest.fixture
def db_session(test_engine):

    connection = test_engine.connect()

    transaction = connection.begin()

    session = Session(
        bind=connection,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session

    finally:
        session.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()


# ============================================================
# TESTCLIENT
# ============================================================

@pytest.fixture
def client(db_session):

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.pop(get_db, None)


# ============================================================
# CENARIO COMPARTILHADO DE CHAMADOS
# ============================================================

@pytest.fixture
def ticket_scenario(db_session):

    unique = uuid4().hex

    # --------------------------------------------------------
    # 1. SETOR
    # --------------------------------------------------------

    sector = Sector(
        name=f"Setor teste {unique}",
        description="Setor criado pelos testes automatizados.",
        is_active=True,
    )

    db_session.add(sector)
    db_session.flush()

    # --------------------------------------------------------
    # 2. PERFIS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 3. PERMISSOES
    # --------------------------------------------------------

    permission_names = [
        PermissionNames.TICKETS_CREATE,
        PermissionNames.TICKETS_READ,
        PermissionNames.TICKETS_READ_ALL,
        PermissionNames.TICKETS_UPDATE,
        PermissionNames.TICKETS_UPDATE_ALL,
        PermissionNames.TICKETS_ASSIGN,
        PermissionNames.TICKETS_RESOLVE,
        PermissionNames.TICKETS_REOPEN,
        PermissionNames.TICKETS_COMMENT,
        PermissionNames.TICKETS_HISTORY_READ,
        PermissionNames.TICKETS_ATTACH,
    ]

    permissions = {}

    for name in permission_names:

        permission = Permission(
            name=name,
            description="Permissao utilizada nos testes.",
            is_active=True,
        )

        db_session.add(permission)

        permissions[name] = permission

    db_session.flush()

    # --------------------------------------------------------
    # 4. PERMISSOES DO ADMINISTRADOR
    # --------------------------------------------------------

    for permission in permissions.values():

        db_session.add(
            ProfilePermission(
                profile_id=admin_profile.id,
                permission_id=permission.id,
                is_active=True,
            )
        )

    # --------------------------------------------------------
    # 5. PERMISSOES DO SOLICITANTE
    # --------------------------------------------------------

    requester_permission_names = [
        PermissionNames.TICKETS_CREATE,
        PermissionNames.TICKETS_READ,
        PermissionNames.TICKETS_UPDATE,
        PermissionNames.TICKETS_REOPEN,
        PermissionNames.TICKETS_HISTORY_READ,
        PermissionNames.TICKETS_ATTACH,
    ]

    # Intencionalmente nao concedemos tickets.comment.
    # Um dos testes verifica se essa ausencia gera HTTP 403.

    for name in requester_permission_names:

        db_session.add(
            ProfilePermission(
                profile_id=requester_profile.id,
                permission_id=permissions[name].id,
                is_active=True,
            )
        )

    db_session.flush()

    # --------------------------------------------------------
    # 6. USUARIOS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 7. STATUS
    # --------------------------------------------------------

    statuses = {}

    for status_name in [
        "Aberto",
        "Em andamento",
        "Resolvido",
        "Reaberto",
    ]:

        ticket_status = TicketStatus(
            name=status_name,
            description=f"Status de teste: {status_name}",
            is_active=True,
        )

        db_session.add(ticket_status)

        statuses[status_name] = ticket_status

    db_session.flush()

    # --------------------------------------------------------
    # 8. PRIORIDADE E CATEGORIA
    # --------------------------------------------------------

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
        ticket_priority,
        ticket_category,
    ])

    db_session.flush()

    # --------------------------------------------------------
    # 9. CHAMADOS
    # --------------------------------------------------------

    own_ticket = Ticket(
        title="Chamado do solicitante",
        description="Chamado criado pelo teste de integracao.",
        status_id=statuses["Aberto"].id,
        priority_id=ticket_priority.id,
        category_id=ticket_category.id,
        requester_id=requester.id,
        assignee_id=None,
    )

    other_ticket = Ticket(
        title="Chamado de outra pessoa",
        description="Chamado utilizado para verificar acesso negado.",
        status_id=statuses["Aberto"].id,
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

    # --------------------------------------------------------
    # 10. TOKENS JWT
    # --------------------------------------------------------

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
        "sector": sector,
        "admin_profile": admin_profile,
        "requester_profile": requester_profile,
        "own_ticket": own_ticket,
        "other_ticket": other_ticket,
        "statuses": statuses,
        "priority": ticket_priority,
        "category": ticket_category,
        "admin_token": admin_token,
        "requester_token": requester_token,
        "other_token": other_token,
    }