from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.schemas.ticket_comment import (
    TicketCommentCreate,
    TicketCommentRead,
)
from app.services.authorization_service import AuthorizationService
from app.services.ticket_access_service import TicketAccessService
from app.services.ticket_comment_service import (
    InvalidTicketCommentError,
    TicketCommentService,
)


router = APIRouter(
    prefix="/tickets",
    tags=["Ticket Comments"],
)


@router.get(
    "/{ticket_id}/comments",
    response_model=list[TicketCommentRead],
)
def list_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketCommentRead]:

    TicketAccessService(db).get_readable_ticket(
        user=current_user,
        ticket_id=ticket_id,
    )

    return TicketCommentService(db).list_comments(ticket_id)


@router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    ticket_id: int,
    data: TicketCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketCommentRead:

    access = TicketAccessService(db)

    access.get_readable_ticket(
        user=current_user,
        ticket_id=ticket_id,
    )

    authorization = AuthorizationService(db)

    if not authorization.has_permission(
        current_user,
        PermissionNames.TICKETS_COMMENT,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui permissao para comentar.",
        )

    try:
        comment = TicketCommentService(db).add_comment(
            ticket_id=ticket_id,
            user_id=current_user.id,
            content=data.content,
        )

        db.commit()

        return comment

    except InvalidTicketCommentError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception:
        db.rollback()
        raise