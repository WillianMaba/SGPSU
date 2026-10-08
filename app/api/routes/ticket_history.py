from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.ticket import Ticket
from app.models.user import User
from app.repositories.ticket_history_repository import (
    TicketHistoryRepository,
)
from app.schemas.ticket_history import TicketHistoryRead


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
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_HISTORY_READ)
    ),
) -> list[TicketHistoryRead]:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado nao encontrado.",
        )

    return TicketHistoryRepository(db).list_by_ticket(ticket_id)