from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.enums import IncidentCategory, IncidentOrigin, IncidentPriority, IncidentStatus, Role


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: Role


class PropertyOut(BaseModel):
    id: int
    name: str
    type: str
    address: str


class UnitOut(BaseModel):
    id: int
    property_id: int
    code: str
    description: str | None


class AttachmentCreate(BaseModel):
    file_name: str = Field(min_length=1)
    file_url: str = Field(min_length=1)


class AttachmentOut(AttachmentCreate):
    id: int
    created_at: datetime


class CommentCreate(BaseModel):
    comment: str = Field(min_length=1)


class CommentOut(BaseModel):
    id: int
    incident_id: int
    user_id: int
    comment: str
    created_at: datetime


class HistoryOut(BaseModel):
    id: int
    action: str
    detail: str
    user_id: int
    created_at: datetime


class IncidentBase(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=5)
    property_id: int
    unit_id: int | None = None
    category: IncidentCategory
    priority: IncidentPriority = IncidentPriority.MEDIUM
    status: IncidentStatus = IncidentStatus.NEW
    assigned_to_id: int | None = None
    opened_at: date
    due_date: date | None = None
    resolved_at: date | None = None
    closed_at: date | None = None
    estimated_cost: Decimal | None = None
    final_cost: Decimal | None = None
    origin: IncidentOrigin


class IncidentCreate(IncidentBase):
    attachments: list[AttachmentCreate] = []


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: IncidentCategory | None = None
    priority: IncidentPriority | None = None
    status: IncidentStatus | None = None
    assigned_to_id: int | None = None
    due_date: date | None = None
    resolved_at: date | None = None
    closed_at: date | None = None
    estimated_cost: Decimal | None = None
    final_cost: Decimal | None = None


class IncidentOut(IncidentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    comments: list[CommentOut] = []
    attachments: list[AttachmentOut] = []
    history: list[HistoryOut] = []


class DashboardOut(BaseModel):
    open_incidents: int
    urgent_incidents: int
    overdue_incidents: int
    incidents_by_property: dict[str, int]
    average_resolution_days: float


class MetaOut(BaseModel):
    users: list[UserOut]
    properties: list[PropertyOut]
