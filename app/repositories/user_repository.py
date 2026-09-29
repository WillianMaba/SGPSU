from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)

        return self.db.scalar(
            statement,
        )

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)

        return self.db.scalar(
            statement,
        )

    def list(self) -> list[User]:
        statement = select(User).order_by(User.id)

        return list(
            self.db.scalars(statement).all(),
        )

    def create(
        self,
        data: UserCreate,
        password_hash: str,
    ) -> User:
        user = User(
            name=data.name,
            email=str(data.email),
            password_hash=password_hash,
            sector_id=data.sector_id,
            profile_id=data.profile_id,
        )

        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)

        return user

    def update(
        self,
        user: User,
        data: UserUpdate,
    ) -> User:
        values = data.model_dump(
            exclude_unset=True,
        )

        if "email" in values and values["email"] is not None:
            values["email"] = str(values["email"])

        for field, value in values.items():
            setattr(
                user,
                field,
                value,
            )

        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)

        return user

    def deactivate(
        self,
        user: User,
    ) -> User:
        user.is_active = False

        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)

        return user