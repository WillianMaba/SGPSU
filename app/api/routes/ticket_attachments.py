import re
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.permissions import PermissionNames
from app.core.storage import (
    MAX_TICKET_ATTACHMENT_SIZE,
    TICKET_STORAGE_DIR,
    resolve_ticket_storage_path,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.ticket_attachment import TicketAttachmentRead
from app.services.authorization_service import AuthorizationService
from app.services.ticket_access_service import TicketAccessService
from app.services.ticket_attachment_service import (
    TicketAttachmentService,
)


router = APIRouter(
    prefix="/tickets",
    tags=["Ticket Attachments"],
)


# LISTAR ANEXOS

@router.get(
    "/{ticket_id}/attachments",
    response_model=list[TicketAttachmentRead],
)
def list_attachments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketAttachmentRead]:

    TicketAccessService(db).get_readable_ticket(
        user=current_user,
        ticket_id=ticket_id,
    )

    return TicketAttachmentService(db).list_attachments(ticket_id)


# ENVIAR ANEXO

@router.post(
    "/{ticket_id}/attachments",
    response_model=TicketAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    ticket_id: int,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketAttachmentRead:

    try:
        # Primeiro verifica se o usuario pode acessar o chamado.
        TicketAccessService(db).get_readable_ticket(
            user=current_user,
            ticket_id=ticket_id,
        )

        # Depois verifica a permissao especifica de anexar.
        authorization = AuthorizationService(db)

        if not authorization.has_permission(
            current_user,
            PermissionNames.TICKETS_ATTACH,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario nao possui permissao para anexar arquivos.",
            )

        original_filename = Path(
            (upload.filename or "").replace("\\", "/")
        ).name

        if not original_filename or len(original_filename) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome de arquivo invalido.",
            )

        contents = await upload.read(
            MAX_TICKET_ATTACHMENT_SIZE + 1
        )

        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo esta vazio.",
            )

        if len(contents) > MAX_TICKET_ATTACHMENT_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="O tamanho maximo do anexo e 10 MB.",
            )

        suffix = Path(original_filename).suffix

        if not re.fullmatch(r"\.[A-Za-z0-9]{1,10}", suffix):
            suffix = ""

        stored_filename = f"{uuid4().hex}{suffix}"

        relative_path = (
            Path("storage") / "tickets" / stored_filename
        ).as_posix()

        file_path = resolve_ticket_storage_path(relative_path)

        TICKET_STORAGE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        # O arquivo usa um nome interno gerado pelo servidor.
        file_path.write_bytes(contents)

        try:
            attachment = TicketAttachmentService(db).add_attachment(
                ticket_id=ticket_id,
                user_id=current_user.id,
                original_filename=original_filename,
                storage_path=relative_path,
                file_size=len(contents),
                mime_type=(
                    upload.content_type
                    or "application/octet-stream"
                ),
            )

            db.commit()

            return attachment

        except Exception:
            db.rollback()
            file_path.unlink(missing_ok=True)
            raise

    finally:
        await upload.close()


# BAIXAR ANEXO

@router.get(
    "/{ticket_id}/attachments/{attachment_id}",
)
def download_attachment(
    ticket_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:

    # A verificacao acontece antes de buscar os dados do anexo.
    TicketAccessService(db).get_readable_ticket(
        user=current_user,
        ticket_id=ticket_id,
    )

    attachment = TicketAttachmentService(db).get_attachment(
        ticket_id=ticket_id,
        attachment_id=attachment_id,
    )

    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anexo nao encontrado.",
        )

    try:
        file_path = resolve_ticket_storage_path(
            attachment.storage_path
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo nao encontrado.",
        ) from exc

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo nao encontrado no armazenamento.",
        )

    return FileResponse(
        path=file_path,
        filename=attachment.original_filename,
        media_type="application/octet-stream",
        content_disposition_type="attachment",
    )