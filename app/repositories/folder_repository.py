from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.folder import Folder


class FolderRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, folder_id: int) -> Folder | None:
        return self.db.get(Folder, folder_id)

    def list_by_repository(
        self,
        repository_id: int,
        parent_folder_id: int | None,
    ) -> list[Folder]:

        statement = (
            select(Folder)
            .where(
                Folder.repository_id == repository_id,
                Folder.parent_folder_id == parent_folder_id,
                Folder.is_active.is_(True),
            )
            .order_by(Folder.name.asc(), Folder.id.asc())
        )

        return list(self.db.scalars(statement).all())

    def create(self, folder: Folder) -> Folder:
        self.db.add(folder)
        self.db.flush()
        self.db.refresh(folder)
        return folder

    def update(self, folder: Folder, values: dict) -> Folder:
        for field, value in values.items():
            setattr(folder, field, value)

        self.db.add(folder)
        self.db.flush()
        self.db.refresh(folder)
        return folder