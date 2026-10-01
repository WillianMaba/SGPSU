from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.sector import Sector
from app.schemas.sector import SectorCreate, SectorUpdate


class SectorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, sector_id: int) -> Sector | None:
        statement = select(Sector).where(
            Sector.id == sector_id,
        )

        return self.db.scalar(statement)

    def get_by_name(self, name: str) -> Sector | None:
        statement = select(Sector).where(
            Sector.name == name,
        )

        return self.db.scalar(statement)

    def list(self) -> list[Sector]:
        statement = select(Sector).order_by(Sector.id)

        return list(
            self.db.scalars(statement).all()
        )

    def create(self, data: SectorCreate) -> Sector:
        sector = Sector(
            name=data.name,
            description=data.description,
            is_active=True,
        )

        self.db.add(sector)
        self.db.flush()
        self.db.refresh(sector)

        return sector

    def update(
        self,
        sector: Sector,
        data: SectorUpdate,
    ) -> Sector:

        values = data.model_dump(
            exclude_unset=True,
        )

        for field, value in values.items():
            setattr(sector, field, value)

        self.db.add(sector)
        self.db.flush()
        self.db.refresh(sector)

        return sector

    def deactivate(self, sector: Sector) -> Sector:
        sector.is_active = False

        self.db.add(sector)
        self.db.flush()
        self.db.refresh(sector)

        return sector