from fastapi import FastAPI

from app.api.incidents import router as incident_router
from app.db.database import Base, engine

app = FastAPI(title="GMAO Incidencias API", version="0.1.0")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


app.include_router(incident_router)


@app.get("/health")
def health():
    return {"status": "ok"}
