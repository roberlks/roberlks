from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.schemas import (
    AttachmentCreate,
    CommentCreate,
    DashboardOut,
    IncidentCreate,
    IncidentOut,
    IncidentUpdate,
)
from app.core.enums import IncidentPriority, IncidentStatus, Role
from app.db.database import get_db
from app.db.models import Incident, IncidentAttachment, IncidentComment, IncidentHistory, Property, User

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _history(db: Session, incident_id: int, user_id: int, action: str, detail: str):
    db.add(IncidentHistory(incident_id=incident_id, user_id=user_id, action=action, detail=detail))


def _incident_to_out(incident: Incident) -> IncidentOut:
    return IncidentOut.model_validate(
        {
            **incident.__dict__,
            "comments": [c.__dict__ for c in sorted(incident.comments, key=lambda x: x.created_at)],
            "attachments": [a.__dict__ for a in incident.attachments],
            "history": [h.__dict__ for h in sorted(incident.history, key=lambda x: x.created_at)],
        }
    )


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    status: IncidentStatus | None = None,
    priority: IncidentPriority | None = None,
    property_id: int | None = None,
    category: str | None = None,
    assigned_to_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = Query(default=None, description="Búsqueda texto en título/descripcion"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = []
    if status:
        filters.append(Incident.status == status)
    if priority:
        filters.append(Incident.priority == priority)
    if property_id:
        filters.append(Incident.property_id == property_id)
    if category:
        filters.append(Incident.category == category)
    if assigned_to_id:
        filters.append(Incident.assigned_to_id == assigned_to_id)
    if date_from:
        filters.append(Incident.opened_at >= date_from)
    if date_to:
        filters.append(Incident.opened_at <= date_to)
    if q:
        filters.append(or_(Incident.title.ilike(f"%{q}%"), Incident.description.ilike(f"%{q}%")))

    query = select(Incident).order_by(Incident.created_at.desc())
    if current_user.role == Role.TECHNICIAN:
        filters.append(Incident.assigned_to_id == current_user.id)
    if filters:
        query = query.where(and_(*filters))
    incidents = db.scalars(query).unique().all()
    return [_incident_to_out(i) for i in incidents]


@router.post("", response_model=IncidentOut)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.MANAGER)),
):
    if payload.due_date and payload.due_date < payload.opened_at:
        raise HTTPException(status_code=400, detail="due_date no puede ser anterior a opened_at")

    incident = Incident(**payload.model_dump(exclude={"attachments"}))
    db.add(incident)
    db.flush()

    for attachment in payload.attachments:
        db.add(IncidentAttachment(incident_id=incident.id, **attachment.model_dump()))

    _history(db, incident.id, current_user.id, "created", "Incidencia creada")
    db.commit()
    db.refresh(incident)
    return _incident_to_out(incident)


@router.get("/dashboard/summary", response_model=DashboardOut)
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    base_filter = []
    if current_user.role == Role.TECHNICIAN:
        base_filter.append(Incident.assigned_to_id == current_user.id)

    open_statuses = [IncidentStatus.NEW, IncidentStatus.UNDER_REVIEW, IncidentStatus.ASSIGNED, IncidentStatus.IN_PROGRESS, IncidentStatus.PENDING_VENDOR]

    open_incidents = db.scalar(select(func.count(Incident.id)).where(Incident.status.in_(open_statuses), *base_filter)) or 0
    urgent_incidents = db.scalar(select(func.count(Incident.id)).where(Incident.priority == IncidentPriority.URGENT, Incident.status.in_(open_statuses), *base_filter)) or 0
    overdue_incidents = db.scalar(select(func.count(Incident.id)).where(Incident.due_date < today, Incident.status.in_(open_statuses), *base_filter)) or 0

    by_property_rows = db.execute(
        select(Property.name, func.count(Incident.id))
        .join(Incident, Incident.property_id == Property.id)
        .where(*base_filter)
        .group_by(Property.name)
    ).all()

    avg_days = db.scalar(
        select(func.avg(func.julianday(Incident.resolved_at) - func.julianday(Incident.opened_at))).where(Incident.resolved_at.is_not(None), *base_filter)
    )

    return DashboardOut(
        open_incidents=open_incidents,
        urgent_incidents=urgent_incidents,
        overdue_incidents=overdue_incidents,
        incidents_by_property={name: total for name, total in by_property_rows},
        average_resolution_days=round(float(avg_days or 0), 2),
    )


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    if current_user.role == Role.TECHNICIAN and incident.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes ver esta incidencia")
    return _incident_to_out(incident)


@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.MANAGER)),
):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)

    _history(db, incident.id, current_user.id, "updated", "Incidencia actualizada")
    db.commit()
    db.refresh(incident)
    return _incident_to_out(incident)


@router.post("/{incident_id}/assign/{user_id}", response_model=IncidentOut)
def assign_incident(
    incident_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.MANAGER)),
):
    incident = db.get(Incident, incident_id)
    user = db.get(User, user_id)
    if not incident or not user:
        raise HTTPException(status_code=404, detail="Incidencia o usuario no encontrado")

    incident.assigned_to_id = user_id
    incident.status = IncidentStatus.ASSIGNED
    _history(db, incident.id, current_user.id, "assigned", f"Asignada a {user.full_name}")
    db.commit()
    db.refresh(incident)
    return _incident_to_out(incident)


@router.post("/{incident_id}/comments")
def add_comment(
    incident_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    if current_user.role == Role.TECHNICIAN and incident.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes comentar esta incidencia")

    comment = IncidentComment(incident_id=incident_id, user_id=current_user.id, comment=payload.comment)
    db.add(comment)
    _history(db, incident.id, current_user.id, "commented", "Nuevo comentario interno")
    db.commit()
    return {"message": "Comentario añadido"}


@router.post("/{incident_id}/attachments", response_model=IncidentOut)
def add_attachment(
    incident_id: int,
    payload: AttachmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.MANAGER)),
):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    db.add(IncidentAttachment(incident_id=incident.id, **payload.model_dump()))
    _history(db, incident.id, current_user.id, "attachment", "Adjunto agregado")
    db.commit()
    db.refresh(incident)
    return _incident_to_out(incident)

