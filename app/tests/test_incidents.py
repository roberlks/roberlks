from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.enums import IncidentCategory, IncidentOrigin, IncidentPriority, IncidentStatus, Role
from app.db.database import Base, get_db
from app.db.models import Property, User
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_data():
    db = TestingSessionLocal()
    db.query(User).delete()
    db.query(Property).delete()
    manager = User(full_name="Manager", email="m@test.com", role=Role.MANAGER)
    tech = User(full_name="Tech", email="t@test.com", role=Role.TECHNICIAN)
    prop = Property(name="Edificio Luna", type="comunidad", address="Calle X")
    db.add_all([manager, tech, prop])
    db.commit()
    db.refresh(manager)
    db.refresh(tech)
    db.refresh(prop)
    db.close()
    return manager.id, tech.id, prop.id


def test_create_assign_and_list_incidents():
    manager_id, tech_id, property_id = setup_data()

    create_payload = {
        "title": "Avería ascensor",
        "description": "El ascensor se queda en planta 2",
        "property_id": property_id,
        "category": IncidentCategory.ELEVATOR,
        "priority": IncidentPriority.URGENT,
        "status": IncidentStatus.NEW,
        "opened_at": str(date.today()),
        "due_date": str(date.today() + timedelta(days=1)),
        "origin": IncidentOrigin.INSPECTION,
        "attachments": [{"file_name": "foto.jpg", "file_url": "https://files/foto.jpg"}],
    }

    created = client.post("/incidents", json=create_payload, headers={"X-User-Id": str(manager_id)})
    assert created.status_code == 200
    incident_id = created.json()["id"]

    assigned = client.post(f"/incidents/{incident_id}/assign/{tech_id}", headers={"X-User-Id": str(manager_id)})
    assert assigned.status_code == 200
    assert assigned.json()["assigned_to_id"] == tech_id

    listed = client.get("/incidents", params={"priority": IncidentPriority.URGENT}, headers={"X-User-Id": str(manager_id)})
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_technician_only_sees_assigned():
    manager_id, tech_id, property_id = setup_data()

    payload = {
        "title": "Limpieza portal",
        "description": "Suciedad en entrada",
        "property_id": property_id,
        "category": IncidentCategory.CLEANING,
        "priority": IncidentPriority.MEDIUM,
        "status": IncidentStatus.NEW,
        "opened_at": str(date.today()),
        "origin": IncidentOrigin.MANAGER,
        "attachments": [],
    }
    created = client.post("/incidents", json=payload, headers={"X-User-Id": str(manager_id)})
    incident_id = created.json()["id"]
    client.post(f"/incidents/{incident_id}/assign/{tech_id}", headers={"X-User-Id": str(manager_id)})

    tech_list = client.get("/incidents", headers={"X-User-Id": str(tech_id)})
    assert tech_list.status_code == 200
    assert all(item["assigned_to_id"] == tech_id for item in tech_list.json())
