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
from app.core.authorization import require_permission
from app.core.permissions import PermissionNames
from app.core.storage import (
    MAX_TICKET_ATTACHMENT_SIZE,
    TICKET_STORAGE_DIR,
    resolve_ticket_storage_path,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.ticket_attachment import TicketAttachmentRead
from app.services.ticket_attachment_service import (
    TicketAttachmentService,
)
from app.services.ticket_comment_service import TicketNotFoundError
from app.models.ticket import Ticket


router = APIRouter(
    prefix="/tickets",
    tags=["Ticket Attachments"],
)


@router.get(
    "/{ticket_id}/attachments",
    response_model=list[TicketAttachmentRead],
)
def list_attachments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_READ)
    ),
) -> list[TicketAttachmentRead]:
    try:
        return TicketAttachmentService(db).list_attachments(ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{ticket_id}/attachments",
    response_model=TicketAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    ticket_id: int,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_ATTACH)
    ),
) -> TicketAttachmentRead:
    service = TicketAttachmentService(db)

    try:
        # Verifica o chamado antes de gravar o arquivo.
        if db.get(Ticket, ticket_id) is None:
            raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Chamado nao encontrado.",
    )

        original_filename = Path(
            (upload.filename or "arquivo").replace("\\", "/")
        ).name

        if not original_filename:
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
        TICKET_STORAGE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        relative_path = (
            Path("storage") / "tickets" / stored_filename
        ).as_posix()

        file_path = resolve_ticket_storage_path(relative_path)
        file_path.write_bytes(contents)

        try:
            attachment = service.add_attachment(
                ticket_id=ticket_id,
                user_id=current_user.id,
                original_filename=original_filename,
                storage_path=relative_path,
                file_size=len(contents),
                mime_type=upload.content_type or "application/octet-stream",
            )

            db.commit()
            return attachment

        except Exception:
            db.rollback()
            file_path.unlink(missing_ok=True)
            raise

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    finally:
        await upload.close()


@router.get(
    "/{ticket_id}/attachments/{attachment_id}",
)
def download_attachment(
    ticket_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PermissionNames.TICKETS_READ)
    ),
) -> FileResponse:
    service = TicketAttachmentService(db)

    try:
        attachment = service.get_attachment(
            ticket_id,
            attachment_id,
        )
    except TicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

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
        media_type=attachment.mime_type,
        content_disposition_type="attachment",
    )