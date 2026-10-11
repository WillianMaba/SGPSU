from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.schemas.ticket import TicketRead
from app.services.authorization_service import AuthorizationService
from app.services.ticket_access_service import TicketAccessService
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


# INICIAR ATENDIMENTO

@router.patch(
    "/{ticket_id}/start",
    response_model=TicketRead,
)
def start_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:

    ticket = TicketAccessService(db).get_readable_ticket(
        user=current_user,
        ticket_id=ticket_id,
    )

    TicketAccessService(db).require_update(
        user=current_user,
        ticket=ticket,
    )

    return execute_transition(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        operation="start",
    )


# RESOLVER CHAMADO

@router.patch(
    "/{ticket_id}/resolve",
    response_model=TicketRead,
)
def resolve_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:

    ticket = TicketAccessService(db).get_readable_ticket(
        user=current_user,
        ticket_id=ticket_id,
    )

    authorization = AuthorizationService(db)

    if not authorization.has_permission(
        current_user,
        PermissionNames.TICKETS_RESOLVE,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui permissao para resolver chamados.",
        )

    TicketAccessService(db).require_update(
        user=current_user,
        ticket=ticket,
    )

    return execute_transition(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        operation="resolve",
    )


# REABRIR CHAMADO

@router.patch(
    "/{ticket_id}/reopen",
    response_model=TicketRead,
)
def reopen_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:

    access = TicketAccessService(db)

    ticket = access.get_readable_ticket(
        user=current_user,
        ticket_id=ticket_id,
    )

    authorization = AuthorizationService(db)

    if not authorization.has_permission(
        current_user,
        PermissionNames.TICKETS_REOPEN,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui permissao para reabrir chamados.",
        )

    is_requester = ticket.requester_id == current_user.id

    if not is_requester:
        access.require_update(
            user=current_user,
            ticket=ticket,
        )

    return execute_transition(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        operation="reopen",
    )