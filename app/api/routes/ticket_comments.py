from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.schemas.ticket_comment import (
    TicketCommentCreate,
    TicketCommentRead,
)
from app.services.ticket_comment_service import (
    InvalidTicketCommentError,
    TicketCommentService,
    TicketNotFoundError,
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
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_READ)
    ),
) -> list[TicketCommentRead]:
    try:
        return TicketCommentService(db).list_comments(ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    ticket_id: int,
    data: TicketCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_COMMENT)
    ),
) -> TicketCommentRead:
    try:
        comment = TicketCommentService(db).add_comment(
            ticket_id=ticket_id,
            user_id=current_user.id,
            content=data.content,
        )

        db.commit()
        return comment

    except TicketNotFoundError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except InvalidTicketCommentError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc