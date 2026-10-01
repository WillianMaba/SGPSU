from sqlalchemy.orm import Session
from app.models.sector import Sector
from app.repositories.sector_repository import SectorRepository
from app.schemas.sector import SectorCreate, SectorUpdate


class SectorAlreadyExistsError(Exception):
    pass


class SectorService:
    def __init__(self, db: Session):
        self.repository = SectorRepository(db)

    def create_sector(self, data: SectorCreate) -> Sector:
        existing_sector = self.repository.get_by_name(
            data.name,
        )

        if existing_sector is not None:
            raise SectorAlreadyExistsError(
                "Ja existe um setor com este nome."
            )

        return self.repository.create(data)

    def get_sector(self, sector_id: int) -> Sector | None:
        return self.repository.get_by_id(sector_id)

    def get_sectors(self) -> list[Sector]:
        return self.repository.list()

    def update_sector(
        self,
        sector: Sector,
        data: SectorUpdate,
    ) -> Sector:

        if data.name is not None:
            existing_sector = self.repository.get_by_name(
                data.name,
            )

            if (
                existing_sector is not None
                and existing_sector.id != sector.id
            ):
                raise SectorAlreadyExistsError(
                    "Ja existe outro setor com este nome."
                )

        return self.repository.update(
            sector=sector,
            data=data,
        )

    def deactivate_sector(self, sector: Sector) -> Sector:
        return self.repository.deactivate(sector)