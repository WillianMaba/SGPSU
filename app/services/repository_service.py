from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.repositories.repository_repository import RepositoryRepository
from app.schemas.repository import RepositoryCreate, RepositoryUpdate


class RepositoryNotFoundError(Exception):
    pass


class RepositoryInvalidUpdateError(Exception):
    pass


class RepositoryService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = RepositoryRepository(db)

    def _get_active(self, repository_id: int) -> Repository:
        repository = self.repository.get_by_id(repository_id)

        if repository is None or not repository.is_active:
            raise RepositoryNotFoundError(
                "Repositorio nao encontrado ou inativo."
            )

        return repository

    def create(self, data: RepositoryCreate) -> Repository:
        repository = Repository(
            name=data.name,
            description=data.description,
            is_active=True,
        )
        return self.repository.create(repository)

    def get(self, repository_id: int) -> Repository:
        return self._get_active(repository_id)

    def list_active(self) -> list[Repository]:
        return self.repository.list_active()

    def update(
        self,
        repository_id: int,
        data: RepositoryUpdate,
    ) -> Repository:

        repository = self._get_active(repository_id)
        values = data.model_dump(exclude_unset=True)

        if not values:
            return repository

        if "name" in values and values["name"] is None:
            raise RepositoryInvalidUpdateError(
                "O nome do repositorio nao pode ser nulo."
            )

        changed_values = {
            field: value
            for field, value in values.items()
            if getattr(repository, field) != value
        }

        if not changed_values:
            return repository

        return self.repository.update(repository, changed_values)