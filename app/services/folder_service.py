from sqlalchemy.orm import Session

from app.models.folder import Folder
from app.models.repository import Repository
from app.repositories.folder_repository import FolderRepository
from app.schemas.folder import FolderCreate, FolderUpdate


class FolderNotFoundError(Exception):
    pass


class FolderReferenceError(Exception):
    pass


class FolderInvalidUpdateError(Exception):
    pass


class FolderService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = FolderRepository(db)

    def _get_active(self, folder_id: int) -> Folder:
        folder = self.repository.get_by_id(folder_id)

        if folder is None or not folder.is_active:
            raise FolderNotFoundError(
                "Pasta nao encontrada ou inativa."
            )

        return folder

    def _validate_repository(self, repository_id: int) -> Repository:
        repository = self.db.get(Repository, repository_id)

        if repository is None or not repository.is_active:
            raise FolderReferenceError(
                "Repositorio nao encontrado ou inativo."
            )

        return repository

    def _validate_parent(
        self,
        repository_id: int,
        parent_folder_id: int | None,
    ) -> Folder | None:

        if parent_folder_id is None:
            return None

        parent = self._get_active(parent_folder_id)

        if parent.repository_id != repository_id:
            raise FolderReferenceError(
                "A pasta pai pertence a outro repositorio."
            )

        return parent

    def _validate_no_cycle(
        self,
        folder: Folder,
        new_parent_id: int | None,
    ) -> None:
        """
        Percorre os ancestrais do novo pai.
        Se encontrar a própria pasta, a movimentação criaria um ciclo.
        """

        current_id = new_parent_id
        visited: set[int] = set()

        while current_id is not None:
            if current_id == folder.id:
                raise FolderInvalidUpdateError(
                    "A pasta nao pode ser movida para dentro dela mesma "
                    "ou de uma pasta descendente."
                )

            if current_id in visited:
                raise FolderInvalidUpdateError(
                    "A hierarquia atual possui um ciclo."
                )

            visited.add(current_id)

            current = self._get_active(current_id)
            current_id = current.parent_folder_id

    def create(
        self,
        repository_id: int,
        data: FolderCreate,
    ) -> Folder:

        self._validate_repository(repository_id)

        self._validate_parent(
            repository_id,
            data.parent_folder_id,
        )

        folder = Folder(
            repository_id=repository_id,
            parent_folder_id=data.parent_folder_id,
            name=data.name,
            description=data.description,
            is_active=True,
        )

        return self.repository.create(folder)

    def get(
        self,
        repository_id: int,
        folder_id: int,
    ) -> Folder:

        folder = self._get_active(folder_id)

        if folder.repository_id != repository_id:
            raise FolderNotFoundError(
                "Pasta nao encontrada neste repositorio."
            )

        return folder

    def list_by_repository(
        self,
        repository_id: int,
        parent_folder_id: int | None = None,
    ) -> list[Folder]:

        self._validate_repository(repository_id)

        self._validate_parent(
            repository_id,
            parent_folder_id,
        )

        return self.repository.list_by_repository(
            repository_id,
            parent_folder_id,
        )

    def update(
        self,
        repository_id: int,
        folder_id: int,
        data: FolderUpdate,
    ) -> Folder:

        folder = self.get(repository_id, folder_id)
        values = data.model_dump(exclude_unset=True)

        if not values:
            return folder

        if "name" in values and values["name"] is None:
            raise FolderInvalidUpdateError(
                "O nome da pasta nao pode ser nulo."
            )

        if "parent_folder_id" in values:
            new_parent_id = values["parent_folder_id"]

            self._validate_parent(
                repository_id,
                new_parent_id,
            )

            self._validate_no_cycle(
                folder,
                new_parent_id,
            )

        changed_values = {
            field: value
            for field, value in values.items()
            if getattr(folder, field) != value
        }

        if not changed_values:
            return folder

        return self.repository.update(folder, changed_values)