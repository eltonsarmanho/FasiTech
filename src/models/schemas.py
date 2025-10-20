from __future__ import annotations

from typing import List

from pydantic import BaseModel, EmailStr


class AccSubmission(BaseModel):
    name: str
    registration: str
    email: EmailStr
    class_group: str
    file_ids: List[str]


Submission = AccSubmission
