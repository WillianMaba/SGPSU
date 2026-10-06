from datetime import datetime
from pydantic import BaseModel


class ProfilePermissionRead(BaseModel):
    profile_id: int
    permission_id: int
    is_active: bool
    created_at: datetime