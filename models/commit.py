from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class Commit(BaseModel):
    id: Optional[int] = None
    hash: str
    author: str
    message: str
    timestamp: datetime
    files_changed: List[str]
    project_id: int

    class Config:
        from_attributes = True