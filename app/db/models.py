from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import IncidentCategory, IncidentOrigin, IncidentPriority, IncidentStatus, Role
from app.db.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    role: Mapped[Role] = mapped_column(Enum(Role))


class Property(TimestampMixin, Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    type: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(300))

    units: Mapped[list["PropertyUnit"]] = relationship(back_populates="property")


class PropertyUnit(TimestampMixin, Base):
    __tablename__ = "property_units"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    code: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    property: Mapped[Property] = relationship(back_populates="units")


class Incident(TimestampMixin, Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("property_units.id"), nullable=True)
    category: Mapped[IncidentCategory] = mapped_column(Enum(IncidentCategory))
    priority: Mapped[IncidentPriority] = mapped_column(Enum(IncidentPriority), default=IncidentPriority.MEDIUM)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.NEW)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    opened_at: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    resolved_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    closed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    final_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    origin: Mapped[IncidentOrigin] = mapped_column(Enum(IncidentOrigin))

    comments: Mapped[list["IncidentComment"]] = relationship(back_populates="incident", cascade="all,delete-orphan")
    attachments: Mapped[list["IncidentAttachment"]] = relationship(back_populates="incident", cascade="all,delete-orphan")
    history: Mapped[list["IncidentHistory"]] = relationship(back_populates="incident", cascade="all,delete-orphan")


class IncidentComment(TimestampMixin, Base):
    __tablename__ = "incident_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    comment: Mapped[str] = mapped_column(Text)

    incident: Mapped[Incident] = relationship(back_populates="comments")


class IncidentAttachment(TimestampMixin, Base):
    __tablename__ = "incident_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    file_name: Mapped[str] = mapped_column(String(200))
    file_url: Mapped[str] = mapped_column(String(500))

    incident: Mapped[Incident] = relationship(back_populates="attachments")


class IncidentHistory(TimestampMixin, Base):
    __tablename__ = "incident_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str] = mapped_column(Text)

    incident: Mapped[Incident] = relationship(back_populates="history")
