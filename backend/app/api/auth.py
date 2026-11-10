import jwt
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidTokenError

from app.db.database import get_db
from app.db.session import settings
from app.services.auth import (
    ALGORITHM,
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user_by_id,
    get_user_by_username,
    get_user_roles,
    get_user_permissions,
)
from app.services.audit import create_audit_event
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    email: Optional[str] = None
    display_name: Optional[str] = None
    department: Optional[str] = "General"


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    clean_username = request.username.strip().lower()
    existing_user = get_user_by_username(db, clean_username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{clean_username}' is already registered",
        )

    # Hash password using Argon2
    hashed_pw = get_password_hash(request.password)

    new_user = User(
        username=clean_username,
        display_name=request.display_name.strip() if request.display_name else clean_username.title(),
        email=request.email.strip().lower() if request.email else f"{clean_username}@easystore.local",
        department=request.department.strip() if request.department else "General",
        password_hash=hashed_pw,
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    # Assign default role (EDITOR or ADMIN if first user)
    default_role = db.query(Role).filter(Role.name == "EDITOR").first()
    if not default_role:
        default_role = Role(name="EDITOR", description="Editor role with read/write access")
        db.add(default_role)
        db.flush()

    user_role = UserRole(user_id=new_user.id, role_id=default_role.id)
    db.add(user_role)

    # Record registration in audit log
    create_audit_event(
        db=db,
        action="USER_REGISTER",
        user_id=new_user.id,
        resource_type="auth",
        resource_id=clean_username,
        success=True,
        details={
            "username": clean_username,
            "department": new_user.department,
            "role": default_role.name,
        },
    )
    db.commit()
    db.refresh(new_user)

    token = create_access_token(new_user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "username": new_user.username,
    }


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    clean_username = request.username.strip().lower()
    user = authenticate_user(
        db,
        clean_username,
        request.password,
    )

    if user is None:
        create_audit_event(
            db=db,
            action="USER_LOGIN_FAILED",
            resource_type="auth",
            resource_id=clean_username,
            success=False,
            error_code="INVALID_CREDENTIALS",
            details={"username": clean_username},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(user.id)

    create_audit_event(
        db=db,
        action="USER_LOGIN",
        user_id=user.id,
        resource_type="auth",
        resource_id=user.username,
        success=True,
        details={"username": user.username},
    )
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
    }


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    user = get_user_by_id(db, user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise credentials_exception

    return user


@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    roles = get_user_roles(db, current_user.id)
    permissions = get_user_permissions(db, current_user.id)

    return {
        "id": current_user.id,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "email": current_user.email,
        "department": current_user.department,
        "roles": [r.name for r in roles],
        "permissions": [p.name for p in permissions],
    }
