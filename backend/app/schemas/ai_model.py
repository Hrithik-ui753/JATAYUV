"""Schemas for AI model version responses."""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class AIModelVersionResponse(BaseModel):
    id: str
    model_name: str
    display_name: str
    version: str
    task_type: str
    description: Optional[str] = None
    accuracy_metrics: Dict[str, Any] = {}
    is_active: bool = True
    loaded_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}

