from datetime import date
from pydantic import BaseModel, Field


class ApplicationBase(BaseModel):
    company: str = Field(min_length=1)
    role: str = Field(min_length=1)
    status: str = Field(pattern="^(applied|interview|rejected|offer)$")
    applied_on: date | None = None


class ApplicationCreate(ApplicationBase):
    user_id: str = Field(min_length=1)


class ApplicationUpdate(BaseModel):
    status: str = Field(pattern="^(applied|interview|rejected|offer)$")


class ApplicationOut(ApplicationBase):
    id: str
    user_id: str
