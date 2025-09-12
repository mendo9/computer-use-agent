from typing import Any

from pydantic import BaseModel


class WorkItem(BaseModel):
    job_id: str
    task: str  # e.g., "fill_login"
    payload: dict[str, Any]  # row data from Excel
