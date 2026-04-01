from datetime import date, timedelta

from app.core.enums import IncidentCategory, IncidentOrigin, IncidentPriority, IncidentStatus, Role
from app.db.database import Base, SessionLocal, engine
from app.db.models import Incident, Property, PropertyUnit, User


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(User).count() > 0:
        print("Seed ya aplicado")
        return

    users = [
        User(full_name="Ana Admin", email="ana@fincas.local", role=Role.ADMIN),
        User(full_name="Gema Gestora", email="gema@fincas.local", role=Role.MANAGER),
        User(full_name="Toni Técnico", email="toni@proveedor.local", role=Role.TECHNICIAN),
        User(full_name="Lola Lectura", email="lola@cliente.local", role=Role.READONLY),
    ]
    db.add_all(users)
    db.flush()

    prop = Property(name="Edificio Sol", type="comunidad", address="Calle Mayor 10, Madrid")
    db.add(prop)
    db.flush()

    unit = PropertyUnit(property_id=prop.id, code="3B", description="Vivienda 3ºB")
    db.add(unit)
    db.flush()

    db.add(
        Incident(
            title="Fuga en baño",
            description="Se reporta humedad en techo del baño por posible fuga",
            property_id=prop.id,
            unit_id=unit.id,
            category=IncidentCategory.PLUMBING,
            priority=IncidentPriority.HIGH,
            status=IncidentStatus.IN_PROGRESS,
            assigned_to_id=users[2].id,
            opened_at=date.today() - timedelta(days=4),
            due_date=date.today() + timedelta(days=2),
            estimated_cost=180,
            origin=IncidentOrigin.TENANT,
        )
    )

    db.commit()
    db.close()
    print("Seed aplicado correctamente")


if __name__ == "__main__":
    run_seed()
