# GMAO / Sistema de Gestión de Incidencias para Property Management

API backend realista para registrar, asignar, seguir y cerrar incidencias de inmuebles (administración de fincas).

## Stack detectado y decisión de integración
El repositorio original no tenía una base de aplicación (solo README de perfil). Para mantener una solución mantenible y extensible se implementó un backend con:
- **FastAPI** (API REST)
- **SQLAlchemy 2.0** (modelo relacional)
- **SQLite** (entorno local rápido, fácilmente migrable)
- **Pytest + TestClient** (tests críticos)

## Arquitectura
```text
app/
  api/
    deps.py          # autenticación simple y permisos por rol
    incidents.py     # endpoints de incidencias + dashboard
    schemas.py       # contratos pydantic
  core/
    enums.py         # catálogos de negocio (estado, prioridad...)
  db/
    database.py      # engine, sesión y dependencia DB
    models.py        # entidades relacionales
  tests/
    test_incidents.py
  main.py            # bootstrap de la API
  seed.py            # datos de ejemplo
```

## Módulo implementado
### Entidades
- `users` (roles: admin, manager, technician, readonly)
- `properties`
- `property_units`
- `incidents`
- `incident_comments`
- `incident_attachments`
- `incident_history`

### Campos mínimos de incidencia cubiertos
- título, descripción, inmueble, unidad opcional
- categoría, prioridad, estado
- responsable asignado
- fecha alta, límite, resolución, cierre
- coste estimado, coste final
- origen
- adjuntos

### Funcionalidades clave
- CRUD de incidencias (crear, listar con filtros, detalle, actualizar)
- Asignación y reasignación de responsable
- Comentarios internos
- Timeline/histórico de actividad automático
- Adjuntos (metadatos)
- Búsqueda por texto (`q` en título/descripcion)
- Dashboard (`/incidents/dashboard/summary`) con:
  - abiertas
  - urgentes
  - vencidas
  - por inmueble
  - tiempo medio de resolución
- Validaciones de datos (Pydantic + reglas de negocio)
- Control de permisos por rol

## Roles y permisos
Se implementó un control simple extensible mediante cabecera `X-User-Id`:
- **admin**: acceso total
- **manager**: crear/editar/asignar/cerrar
- **technician**: ver y comentar solo incidencias asignadas
- **readonly**: lectura

## Endpoints principales
- `GET /health`
- `GET /incidents` (filtros: `status`, `priority`, `property_id`, `category`, `assigned_to_id`, `date_from`, `date_to`, `q`)
- `POST /incidents`
- `GET /incidents/{incident_id}`
- `PATCH /incidents/{incident_id}`
- `POST /incidents/{incident_id}/assign/{user_id}`
- `POST /incidents/{incident_id}/comments`
- `POST /incidents/{incident_id}/attachments`
- `GET /incidents/dashboard/summary`

## Ejecución local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload
```

## Seeds
```bash
python -m app.seed
```

## Tests
```bash
pytest
```

## Próximas mejoras recomendadas
1. Sustituir `X-User-Id` por JWT/OAuth real.
2. Añadir migraciones versionadas (Alembic).
3. Subida real de archivos (S3/Blob) y antivirus.
4. Notificaciones por email/WhatsApp/webhook ante cambios de estado.
5. Frontend operacional (kanban + calendario SLA + vista móvil).


## Frontend de prueba rápida
Se añadió un frontend estático para usar la API sin Postman:
- URL: `http://127.0.0.1:8000/`
- Selecciona usuario para simular permisos (`X-User-Id`).
- Permite ver dashboard, listar incidencias y crear nuevas.

### Flujo recomendado
```bash
python -m app.seed
uvicorn app.main:app --reload
```
Luego abre `http://127.0.0.1:8000/` desde tu navegador.
