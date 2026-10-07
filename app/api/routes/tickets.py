from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.services.ticket_service import (
    TicketReferenceNotFoundError,
    TicketService,
)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.post(
    "/",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.TICKETS_CREATE
        )
    ),
) -> TicketRead:

    service = TicketService(db)

    try:
        ticket = service.create_ticket(
            data=data,
            requester_id=current_user.id,
        )

        db.commit()

        return ticket

    except TicketReferenceNotFoundError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Os dados informados violam uma regra de integridade do banco.",
        ) from exc


@router.get(
    "/",
    response_model=list[TicketRead],
)
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.TICKETS_READ
        )
    ),
) -> list[TicketRead]:

    return TicketService(db).get_tickets()


@router.get(
    "/{ticket_id}",
    response_model=TicketRead,
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.TICKETS_READ
        )
    ),
) -> TicketRead:

    ticket = TicketService(db).get_ticket(
        ticket_id,
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado nao encontrado.",
        )

    return ticket


@router.patch(
    "/{ticket_id}",
    response_model=TicketRead,
)
def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            PermissionNames.TICKETS_UPDATE
        )
    ),
) -> TicketRead:

    service = TicketService(db)

    ticket = service.get_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado nao encontrado.",
        )

    try:
        updated_ticket = service.update_ticket(
            ticket=ticket,
            data=data,
        )

        db.commit()

        return updated_ticket

    except TicketReferenceNotFoundError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Os dados informados violam uma regra de integridade do banco.",
        ) from exc