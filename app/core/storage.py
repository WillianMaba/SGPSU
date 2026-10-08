from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TICKET_STORAGE_DIR = PROJECT_ROOT / "storage" / "tickets"

MAX_TICKET_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB


def resolve_ticket_storage_path(relative_path: str) -> Path:
    storage_root = TICKET_STORAGE_DIR.resolve()
    candidate = (PROJECT_ROOT / relative_path).resolve()

    try:
        candidate.relative_to(storage_root)
    except ValueError as exc:
        raise ValueError(
            "Caminho de armazenamento invalido."
        ) from exc

    return candidate