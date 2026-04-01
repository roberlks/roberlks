from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    TECHNICIAN = "technician"
    READONLY = "readonly"


class IncidentCategory(StrEnum):
    PLUMBING = "fontaneria"
    ELECTRICITY = "electricidad"
    LOCKS = "cerraduras"
    CLEANING = "limpieza"
    DAMAGES = "danos"
    HVAC = "climatizacion"
    ELEVATOR = "ascensor"
    SECURITY = "seguridad"
    OTHER = "otros"


class IncidentPriority(StrEnum):
    LOW = "baja"
    MEDIUM = "media"
    HIGH = "alta"
    URGENT = "urgente"


class IncidentStatus(StrEnum):
    NEW = "nueva"
    UNDER_REVIEW = "en_revision"
    ASSIGNED = "asignada"
    IN_PROGRESS = "en_curso"
    PENDING_VENDOR = "pendiente_proveedor"
    RESOLVED = "resuelta"
    CLOSED = "cerrada"
    CANCELED = "cancelada"


class IncidentOrigin(StrEnum):
    TENANT = "inquilino"
    OWNER = "propietario"
    MANAGER = "administrador"
    INSPECTION = "inspeccion"
    PREVENTIVE_MAINTENANCE = "mantenimiento_preventivo"
