from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Action(BaseModel):
    action_type: str
    target: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
