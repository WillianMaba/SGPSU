from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.repository import Repository


class RepositoryRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, repository_id: int) -> Repository | None:
        return self.db.get(Repository, repository_id)

    def list_active(self) -> list[Repository]:
        statement = (
            select(Repository)
            .where(Repository.is_active.is_(True))
            .order_by(Repository.name.asc(), Repository.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def create(self, repository: Repository) -> Repository:
        self.db.add(repository)
        self.db.flush()
        self.db.refresh(repository)
        return repository

    def update(self, repository: Repository, values: dict) -> Repository:
        for field, value in values.items():
            setattr(repository, field, value)

        self.db.add(repository)
        self.db.flush()
        self.db.refresh(repository)
        return repository