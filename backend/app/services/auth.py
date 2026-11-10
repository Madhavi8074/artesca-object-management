from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import settings
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole

ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def get_user_by_username(
    db: Session,
    username: str,
):
    return db.scalar(
        select(User).where(
            User.username == username
        )
    )


def get_user_by_id(
    db: Session,
    user_id: int,
):
    return db.scalar(
        select(User).where(
            User.id == user_id
        )
    )


def get_user_roles(
    db: Session,
    user_id: int,
):
    return db.scalars(
        select(Role)
        .join(
            UserRole,
            UserRole.role_id == Role.id,
        )
        .where(
            UserRole.user_id == user_id
        )
    ).all()


def get_user_permissions(
    db: Session,
    user_id: int,
):
    return db.scalars(
        select(Permission)
        .join(
            RolePermission,
            RolePermission.permission_id == Permission.id,
        )
        .join(
            UserRole,
            UserRole.role_id == RolePermission.role_id,
        )
        .where(
            UserRole.user_id == user_id
        )
        .distinct()
    ).all()


def user_has_permission(
    db: Session,
    user_id: int,
    permission_name: str,
) -> bool:
    permission = db.scalar(
        select(Permission)
        .join(
            RolePermission,
            RolePermission.permission_id == Permission.id,
        )
        .join(
            UserRole,
            UserRole.role_id == RolePermission.role_id,
        )
        .where(
            UserRole.user_id == user_id,
            Permission.name == permission_name,
        )
    )

    return permission is not None


def authenticate_user(
    db: Session,
    username: str,
    password: str,
):
    user = get_user_by_username(
        db,
        username,
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not user.password_hash:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def require_user(user):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )

    return user
