from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.incidents import router as incident_router
from app.db.database import Base, engine

app = FastAPI(title="GMAO Incidencias API", version="0.1.0")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


app.include_router(incident_router)

frontend_dir = Path(__file__).parent / "frontend"
app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


@app.get("/", include_in_schema=False)
def frontend_index():
    return FileResponse(frontend_dir / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
