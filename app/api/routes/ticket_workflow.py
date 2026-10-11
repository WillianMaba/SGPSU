from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.schemas.ticket import TicketRead
from app.services.ticket_service import (
    TicketInvalidTransitionError,
    TicketNotFoundError,
    TicketService,
)


router = APIRouter(
    prefix="/tickets",
    tags=["Ticket Workflow"],
)


def execute_transition(
    db: Session,
    ticket_id: int,
    user_id: int,
    operation: str,
):
    service = TicketService(db)

    try:
        if operation == "start":
            ticket = service.start_ticket(ticket_id, user_id)

        elif operation == "resolve":
            ticket = service.resolve_ticket(ticket_id, user_id)

        elif operation == "reopen":
            ticket = service.reopen_ticket(ticket_id, user_id)

        else:
            raise ValueError(
                "Operacao de atendimento desconhecida."
            )

        db.commit()
        return ticket

    except TicketNotFoundError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except TicketInvalidTransitionError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.patch(
    "/{ticket_id}/start",
    response_model=TicketRead,
)
def start_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_UPDATE)
    ),
) -> TicketRead:

    return execute_transition(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        operation="start",
    )


@router.patch(
    "/{ticket_id}/resolve",
    response_model=TicketRead,
)
def resolve_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_RESOLVE)
    ),
) -> TicketRead:

    return execute_transition(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        operation="resolve",
    )


@router.patch(
    "/{ticket_id}/reopen",
    response_model=TicketRead,
)
def reopen_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_REOPEN)
    ),
) -> TicketRead:

    return execute_transition(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        operation="reopen",
    )