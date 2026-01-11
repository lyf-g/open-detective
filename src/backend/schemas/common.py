from pydantic import BaseModel
from typing import Optional, Any

class BaseError(BaseModel):
    code: int
    message: str
    details: Optional[Any] = None
