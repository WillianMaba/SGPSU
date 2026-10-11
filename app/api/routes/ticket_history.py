from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.repositories.ticket_history_repository import (
    TicketHistoryRepository,
)
from app.schemas.ticket_history import TicketHistoryRead
from app.services.authorization_service import AuthorizationService
from app.services.ticket_access_service import TicketAccessService


router = APIRouter(
    prefix="/tickets",
    tags=["Ticket History"],
)


@router.get(
    "/{ticket_id}/history",
    response_model=list[TicketHistoryRead],
)
def list_ticket_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketHistoryRead]:

    TicketAccessService(db).get_readable_ticket(
        user=current_user,
        ticket_id=ticket_id,
    )

    authorization = AuthorizationService(db)

    if not authorization.has_permission(
        current_user,
        PermissionNames.TICKETS_HISTORY_READ,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui permissao para consultar o historico.",
        )

    return TicketHistoryRepository(db).list_by_ticket(ticket_id)