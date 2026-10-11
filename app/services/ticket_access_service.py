from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import PermissionNames
from app.models.ticket import Ticket
from app.models.user import User
from app.services.authorization_service import AuthorizationService


class TicketAccessService:

    def __init__(self, db: Session):
        self.db = db
        self.authorization = AuthorizationService(db)

    def can_read(
        self,
        user: User,
        ticket: Ticket,
    ) -> bool:

        if self.authorization.has_permission(
            user,
            PermissionNames.TICKETS_READ_ALL,
        ):
            return True

        if not self.authorization.has_permission(
            user,
            PermissionNames.TICKETS_READ,
        ):
            return False

        return (
            ticket.requester_id == user.id
            or ticket.assignee_id == user.id
        )

    def can_update(
        self,
        user: User,
        ticket: Ticket,
    ) -> bool:

        if self.authorization.has_permission(
            user,
            PermissionNames.TICKETS_UPDATE_ALL,
        ):
            return True

        if not self.authorization.has_permission(
            user,
            PermissionNames.TICKETS_UPDATE,
        ):
            return False

        return ticket.assignee_id == user.id

    def require_read(
        self,
        user: User,
        ticket: Ticket,
    ) -> None:

        if not self.can_read(user, ticket):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chamado nao encontrado.",
            )

    def require_update(
        self,
        user: User,
        ticket: Ticket,
    ) -> None:

        if not self.can_update(user, ticket):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Usuario nao possui autorizacao "
                    "para alterar este chamado."
                ),
            )
            
    def get_readable_ticket(
        self,
        user: User,
        ticket_id: int,
    ) -> Ticket:

        ticket = self.db.get(Ticket, ticket_id)

        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chamado nao encontrado.",
            )

        self.require_read(
            user=user,
            ticket=ticket,
        )

        return ticket        