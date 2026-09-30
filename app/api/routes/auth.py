from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.security import (
    create_access_token,
    decode_access_token,
)
from app.db.session import get_db
from app.schemas.auth import Token
from app.services.user_service import (
    InvalidCredentialsError,
    UserService,
)
from jwt.exceptions import InvalidTokenError
from app.models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
)


@router.post(
    "/token",
    response_model=Token,
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    db: Session = Depends(get_db),
) -> Token:
    service = UserService(db)

    try:
        user = service.authenticate_user(
            email=form_data.username,
            password=form_data.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    access_token = create_access_token(
        subject=str(user.id),
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
    )
    
    def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nao foi possivel validar as credenciais.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = decode_access_token(token)

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ) as exc:
        raise credentials_exception from exc

    user = UserService(db).get_user(user_id)

    if user is None or not user.is_active:
        raise credentials_exception

    return user