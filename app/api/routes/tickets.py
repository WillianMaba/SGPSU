from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.routes.auth import get_current_user
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.db.session import get_db
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.services.authorization_service import AuthorizationService
from app.services.ticket_access_service import TicketAccessService
from app.services.ticket_service import (
    TicketInvalidTransitionError,
    TicketInvalidUpdateError,
    TicketReferenceNotFoundError,
    TicketService,
)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


# CRIAR CHAMADO

@router.post(
    "/",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_CREATE)
    ),
) -> TicketRead:

    if data.assignee_id is not None:
        authorization = AuthorizationService(db)

        if not authorization.has_permission(
            current_user,
            PermissionNames.TICKETS_ASSIGN,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Usuario nao possui permissao "
                    "para atribuir chamados."
                ),
            )

    service = TicketService(db)

    try:
        ticket = service.create_ticket(
            data=data,
            requester_id=current_user.id,
        )

        db.commit()

        return ticket

    except TicketInvalidTransitionError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

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


# LISTAR CHAMADOS

@router.get(
    "/",
    response_model=list[TicketRead],
)
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_READ)
    ),
) -> list[TicketRead]:

    service = TicketService(db)

    authorization = AuthorizationService(db)

    if authorization.has_permission(
        current_user,
        PermissionNames.TICKETS_READ_ALL,
    ):
        return service.get_tickets()

    return service.repository.list_visible_to_user(
        current_user.id,
    )


# CONSULTAR CHAMADO POR ID

@router.get(
    "/{ticket_id}",
    response_model=TicketRead,
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:

    ticket = TicketService(db).get_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado nao encontrado.",
        )

    TicketAccessService(db).require_read(
        user=current_user,
        ticket=ticket,
    )

    return ticket


# ATUALIZAR CHAMADO

@router.patch(
    "/{ticket_id}",
    response_model=TicketRead,
)
def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:

    service = TicketService(db)

    ticket = service.get_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado nao encontrado.",
        )

    # Verifica se o usuario pode editar ESTE chamado.
    TicketAccessService(db).require_update(
        user=current_user,
        ticket=ticket,
    )

    values = data.model_dump(exclude_unset=True)

    # Alterar o responsavel exige uma permissao adicional.
    if "assignee_id" in values:

        authorization = AuthorizationService(db)

        can_assign = authorization.has_permission(
            user=current_user,
            permission_name=PermissionNames.TICKETS_ASSIGN,
        )

        if not can_assign:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Usuario nao possui permissao "
                    "para atribuir chamados."
                ),
            )

    try:
        updated_ticket = service.update_ticket(
            ticket=ticket,
            data=data,
            changed_by_id=current_user.id,
        )

        db.commit()

        return updated_ticket

    except TicketInvalidUpdateError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

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
            detail=(
                "Os dados informados violam uma regra "
                "de integridade do banco."
            ),
        ) from exc