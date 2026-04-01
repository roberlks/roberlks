from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import Role
from app.db.database import get_db
from app.db.models import User


ROLE_HIERARCHY = {
    Role.READONLY: 1,
    Role.TECHNICIAN: 2,
    Role.MANAGER: 3,
    Role.ADMIN: 4,
}


def get_current_user(x_user_id: int | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Header X-User-Id requerido")
    user = db.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido")
    return user


def require_role(min_role: Role):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if ROLE_HIERARCHY[current_user.role] < ROLE_HIERARCHY[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        return current_user

    return checker
