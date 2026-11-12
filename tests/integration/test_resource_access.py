
import pytest

from app.models.file import File
from app.models.file_access import FileAccess
from app.models.folder import Folder
from app.models.folder_access import FolderAccess
from app.models.profile import Profile
from app.models.repository import Repository
from app.models.repository_access import RepositoryAccess
from app.models.sector import Sector
from app.models.user import User
from app.services.resource_access_service import ResourceAccessService
from sqlalchemy import update

from app.services.resource_access_service import (
    ResourceAccessError,
    ResourceAccessService,
)


@pytest.fixture
def resource_scenario(db_session):
    sector = Sector(
        name="Setor ACL Teste",
        is_active=True,
    )
    profile = Profile(
        name="Perfil ACL Teste",
        is_active=True,
    )

    db_session.add_all([sector, profile])
    db_session.flush()

    user = User(
        name="Usuário ACL",
        email="acl.teste@example.com",
        password_hash="hash-de-teste",
        sector_id=sector.id,
        profile_id=profile.id,
        is_active=True,
    )

    repository = Repository(
        name="Repositório ACL Teste",
        description="Repositório para testes de autorização",
        is_active=True,
    )

    db_session.add_all([user, repository])
    db_session.flush()

    root_folder = Folder(
        repository_id=repository.id,
        name="Pasta Principal",
        is_active=True,
    )

    db_session.add(root_folder)
    db_session.flush()

    child_folder = Folder(
        repository_id=repository.id,
        parent_folder_id=root_folder.id,
        name="Subpasta",
        is_active=True,
    )

    db_session.add(child_folder)
    db_session.flush()

    file = File(
        folder_id=child_folder.id,
        name="documento-teste.pdf",
        storage_path="testes/documento-teste.pdf",
        file_size=1024,
        mime_type="application/pdf",
        created_by_id=user.id,
        is_active=True,
    )

    db_session.add(file)
    db_session.flush()

    return {
        "user": user,
        "sector": sector,
        "profile": profile,
        "repository": repository,
        "root_folder": root_folder,
        "child_folder": child_folder,
        "file": file,
        "service": ResourceAccessService(db_session),
        "db": db_session,
    }


def add_repository_rule(
    scenario,
    permission,
    effect="ALLOW",
    user_id=None,
    profile_id=None,
    sector_id=None,
    is_active=True,
):
    rule = RepositoryAccess(
        repository_id=scenario["repository"].id,
        user_id=user_id,
        profile_id=profile_id,
        sector_id=sector_id,
        permission=permission,
        effect=effect,
        is_active=is_active,
    )
    scenario["db"].add(rule)
    scenario["db"].flush()
    return rule


def add_folder_rule(
    scenario,
    permission,
    effect="ALLOW",
    folder=None,
    user_id=None,
    profile_id=None,
    sector_id=None,
    is_active=True,
):
    rule = FolderAccess(
        folder_id=(folder or scenario["root_folder"]).id,
        user_id=user_id,
        profile_id=profile_id,
        sector_id=sector_id,
        permission=permission,
        effect=effect,
        is_active=is_active,
    )
    scenario["db"].add(rule)
    scenario["db"].flush()
    return rule


def add_file_rule(
    scenario,
    permission,
    effect="ALLOW",
    user_id=None,
    profile_id=None,
    sector_id=None,
    is_active=True,
):
    rule = FileAccess(
        file_id=scenario["file"].id,
        user_id=user_id,
        profile_id=profile_id,
        sector_id=sector_id,
        permission=permission,
        effect=effect,
        is_active=is_active,
    )
    scenario["db"].add(rule)
    scenario["db"].flush()
    return rule


def test_access_is_denied_without_any_rule(resource_scenario):
    scenario = resource_scenario

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is False


def test_repository_permission_is_inherited_by_folder_and_file(
    resource_scenario,
):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is True

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["root_folder"],
        "READ",
    ) is True

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is True


def test_profile_permission_grants_access(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        profile_id=scenario["profile"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is True


def test_sector_permission_grants_access(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        sector_id=scenario["sector"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is True


def test_folder_permission_is_inherited_by_child_folder_and_file(
    resource_scenario,
):
    scenario = resource_scenario

    add_folder_rule(
        scenario,
        permission="READ",
        folder=scenario["root_folder"],
        user_id=scenario["user"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["child_folder"],
        "READ",
    ) is True

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is True


def test_file_permission_grants_access_only_to_file(resource_scenario):
    scenario = resource_scenario

    add_file_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is True

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is False

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["root_folder"],
        "READ",
    ) is False


def test_deny_in_folder_overrides_repository_allow(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        effect="ALLOW",
        user_id=scenario["user"].id,
    )

    add_folder_rule(
        scenario,
        permission="READ",
        effect="DENY",
        folder=scenario["root_folder"],
        user_id=scenario["user"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is True

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["root_folder"],
        "READ",
    ) is False

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is False


def test_deny_in_file_overrides_inherited_repository_allow(
    resource_scenario,
):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        effect="ALLOW",
        user_id=scenario["user"].id,
    )

    add_file_rule(
        scenario,
        permission="READ",
        effect="DENY",
        user_id=scenario["user"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is True

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is False


def test_admin_allow_grants_read_access(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="ADMIN",
        effect="ALLOW",
        user_id=scenario["user"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is True

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "WRITE",
    ) is True

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "ADMIN",
    ) is True


def test_inactive_access_rule_is_ignored(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
        is_active=False,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is False


def test_inactive_user_cannot_access_resources(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
    )

    scenario["user"].is_active = False
    scenario["db"].flush()

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is False


def test_inactive_repository_blocks_access(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
    )

    scenario["repository"].is_active = False
    scenario["db"].flush()

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is False


def test_inactive_folder_blocks_access_to_its_file(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
    )

    scenario["child_folder"].is_active = False
    scenario["db"].flush()

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is False


def test_inactive_file_blocks_access(resource_scenario):
    scenario = resource_scenario

    add_file_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
    )

    scenario["file"].is_active = False
    scenario["db"].flush()

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is False


def test_invalid_permission_is_denied(resource_scenario):
    scenario = resource_scenario

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "INVALID_PERMISSION",
    ) is False


def test_shortcut_methods_check_expected_permissions(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
    )

    assert scenario["service"].can_read(
        scenario["user"],
        scenario["repository"],
    ) is True

    assert scenario["service"].can_write(
        scenario["user"],
        scenario["repository"],
    ) is False

    assert scenario["service"].can_modify(
        scenario["user"],
        scenario["repository"],
    ) is False

    assert scenario["service"].can_delete(
        scenario["user"],
        scenario["repository"],
    ) is False

    assert scenario["service"].can_admin(
        scenario["user"],
        scenario["repository"],
    ) is False


def test_deny_admin_overrides_inherited_allow(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="ADMIN",
        effect="DENY",
        user_id=scenario["user"].id,
    )

    add_folder_rule(
        scenario,
        permission="READ",
        effect="ALLOW",
        folder=scenario["root_folder"],
        user_id=scenario["user"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is False


def test_deny_in_child_folder_overrides_parent_allow(resource_scenario):
    scenario = resource_scenario

    add_folder_rule(
        scenario,
        permission="READ",
        effect="ALLOW",
        folder=scenario["root_folder"],
        user_id=scenario["user"].id,
    )

    add_folder_rule(
        scenario,
        permission="READ",
        effect="DENY",
        folder=scenario["child_folder"],
        user_id=scenario["user"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["root_folder"],
        "READ",
    ) is True

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is False


def test_deny_from_sector_overrides_user_and_profile_allows(
    resource_scenario,
):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        effect="ALLOW",
        user_id=scenario["user"].id,
    )

    add_repository_rule(
        scenario,
        permission="READ",
        effect="ALLOW",
        profile_id=scenario["profile"].id,
    )

    add_repository_rule(
        scenario,
        permission="READ",
        effect="DENY",
        sector_id=scenario["sector"].id,
    )

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["repository"],
        "READ",
    ) is False


def test_circular_folder_hierarchy_denies_access(resource_scenario):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
    )

    # Cria um ciclo: a pasta principal passa a apontar para sua subpasta.
    scenario["db"].execute(
        update(Folder)
        .where(Folder.id == scenario["root_folder"].id)
        .values(parent_folder_id=scenario["child_folder"].id)
    )

    scenario["db"].expire_all()

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is False


def test_require_access_raises_error_without_permission(resource_scenario):
    scenario = resource_scenario

    with pytest.raises(
        ResourceAccessError,
        match="Usuario nao possui acesso a este recurso",
    ):
        scenario["service"].require_access(
            scenario["user"],
            scenario["repository"],
            "READ",
        )


def test_inactive_repository_blocks_access_to_its_file(
    resource_scenario,
):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
    )

    scenario["repository"].is_active = False
    scenario["db"].flush()

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is False


def test_folder_from_another_repository_invalidates_hierarchy(
    resource_scenario,
):
    scenario = resource_scenario

    add_repository_rule(
        scenario,
        permission="READ",
        user_id=scenario["user"].id,
    )

    another_repository = Repository(
        name="Outro Repositório ACL",
        description="Repositório para testar hierarquia inconsistente",
        is_active=True,
    )

    scenario["db"].add(another_repository)
    scenario["db"].flush()

    another_folder = Folder(
        repository_id=another_repository.id,
        name="Pasta de Outro Repositório",
        is_active=True,
    )

    scenario["db"].add(another_folder)
    scenario["db"].flush()

    # A subpasta passa a apontar para uma pasta de outro repositório.
    scenario["db"].execute(
        update(Folder)
        .where(Folder.id == scenario["child_folder"].id)
        .values(parent_folder_id=another_folder.id)
    )

    scenario["db"].expire_all()

    assert scenario["service"].can_access(
        scenario["user"],
        scenario["file"],
        "READ",
    ) is False
