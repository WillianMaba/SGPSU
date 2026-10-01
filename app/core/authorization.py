from collections.abc import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.routes.auth import get_current_user
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.services.authorization_service import AuthorizationService


def require_permission(
    permission_name: str,
) -> Callable:

    def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:

        authorization_service = AuthorizationService(db)

        has_permission = authorization_service.has_permission(
            user=current_user,
            permission_name=permission_name,
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario nao possui permissao para esta operacao.",
            )

        return current_user

    return permission_dependency