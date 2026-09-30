from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def create_user(self, data: UserCreate) -> User:
        existing_user = self.repository.get_by_email(str(data.email))

        if existing_user is not None:
            raise UserAlreadyExistsError(
                "Ja existe um usuario com este e-mail."
            )

        password_hash_value = hash_password(data.password)

        return self.repository.create(
            data=data,
            password_hash=password_hash_value,
        )

    def get_user(self, user_id: int) -> User | None:
        return self.repository.get_by_id(user_id)

    def get_users(self) -> list[User]:
        return self.repository.list()

    def update_user(
        self,
        user: User,
        data: UserUpdate,
    ) -> User:

        if data.email is not None:
            existing_user = self.repository.get_by_email(
                str(data.email)
            )

            if existing_user is not None and existing_user.id != user.id:
                raise UserAlreadyExistsError(
                    "Ja existe outro usuario com este e-mail."
                )

        return self.repository.update(
            user=user,
            data=data,
        )

    def deactivate_user(self, user: User) -> User:
        return self.repository.deactivate(user)

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> User:

        user = self.repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError(
                "Credenciais invalidas."
            )

        if not user.is_active:
            raise InvalidCredentialsError(
                "Credenciais invalidas."
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise InvalidCredentialsError(
                "Credenciais invalidas."
            )

        return user