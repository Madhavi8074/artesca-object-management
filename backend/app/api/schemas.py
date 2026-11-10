import re
from datetime import datetime, date
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.metadata_schema import MetadataSchema
from app.models.user import User
from app.services.audit import create_audit_event
from app.services.permissions import require_permission

router = APIRouter(
    prefix="/api/v1/schemas",
    tags=["Metadata Schemas"],
    dependencies=[Depends(get_current_user)],
)


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

ALLOWED_FIELD_TYPES = ["string", "number", "boolean", "date", "enum"]


class SchemaFieldDefinition(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=200)
    type: str = Field(default="string")
    required: bool = False
    options: List[str] = Field(default_factory=list)
    default_value: Optional[Any] = None
    validation_regex: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^[a-zA-Z0-9_]+$", clean):
            raise ValueError("Field name must contain only letters, numbers, and underscores")
        return clean

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_FIELD_TYPES:
            raise ValueError(f"Field type must be one of: {', '.join(ALLOWED_FIELD_TYPES)}")
        return clean


class MetadataSchemaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    version: str = Field(default="1.0", max_length=20)
    is_active: bool = True
    fields: List[SchemaFieldDefinition] = Field(default_factory=list)


class MetadataSchemaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    fields: Optional[List[SchemaFieldDefinition]] = None


class MetadataValidationRequest(BaseModel):
    metadata: dict[str, Any]


# ============================================================
# HELPER: VALIDATE PAYLOAD AGAINST SCHEMA FIELDS
# ============================================================

def validate_payload_against_schema(schema: MetadataSchema, payload: dict[str, Any]) -> List[str]:
    errors: List[str] = []
    field_defs = schema.fields or []

    for f in field_defs:
        fname = f.get("name")
        flabel = f.get("label", fname)
        ftype = f.get("type", "string")
        frequired = f.get("required", False)
        foptions = f.get("options", [])
        fregex = f.get("validation_regex")
        fmin = f.get("min_value")
        fmax = f.get("max_value")

        val = payload.get(fname)

        # Check required
        if frequired and (val is None or val == ""):
            errors.append(f"Field '{flabel}' ({fname}) is required.")
            continue

        if val is None or val == "":
            continue

        # Type checks
        if ftype == "number":
            try:
                num_val = float(val)
                if fmin is not None and num_val < fmin:
                    errors.append(f"Field '{flabel}' must be at least {fmin}.")
                if fmax is not None and num_val > fmax:
                    errors.append(f"Field '{flabel}' must be at most {fmax}.")
            except (ValueError, TypeError):
                errors.append(f"Field '{flabel}' must be a valid number.")

        elif ftype == "boolean":
            if not isinstance(val, bool) and str(val).lower() not in ("true", "false", "1", "0"):
                errors.append(f"Field '{flabel}' must be true or false.")

        elif ftype == "enum":
            if foptions and str(val) not in foptions:
                errors.append(f"Field '{flabel}' must be one of: {', '.join(foptions)}.")

        elif ftype == "date":
            if isinstance(val, (datetime, date)):
                pass
            else:
                try:
                    datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"Field '{flabel}' must be a valid ISO date (YYYY-MM-DD).")

        elif ftype == "string":
            str_val = str(val)
            if fregex:
                try:
                    if not re.search(fregex, str_val):
                        errors.append(f"Field '{flabel}' does not match required pattern.")
                except re.error:
                    pass

    return errors


# ============================================================
# ENDPOINTS
# ============================================================

@router.get(
    "/",
    dependencies=[Depends(require_permission("SCHEMA_READ"))],
)
def list_schemas(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    query = db.query(MetadataSchema)
    if is_active is not None:
        query = query.filter(MetadataSchema.is_active == is_active)

    schemas = query.order_by(MetadataSchema.name).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "version": s.version,
            "is_active": s.is_active,
            "field_count": len(s.fields) if s.fields else 0,
            "fields": s.fields,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in schemas
    ]


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("SCHEMA_WRITE"))],
)
def create_schema(
    payload: MetadataSchemaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(MetadataSchema).filter(MetadataSchema.name == payload.name.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Metadata schema with name '{payload.name}' already exists",
        )

    # Check for duplicate field names
    names = [f.name for f in payload.fields]
    if len(names) != len(set(names)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field names within a schema must be unique",
        )

    schema = MetadataSchema(
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        version=payload.version,
        is_active=payload.is_active,
        fields=[f.model_dump() for f in payload.fields],
    )
    db.add(schema)
    db.flush()

    create_audit_event(
        db=db,
        action="SCHEMA_CREATE",
        user_id=current_user.id,
        resource_type="schema",
        resource_id=str(schema.id),
        success=True,
        details={"name": schema.name, "field_count": len(schema.fields)},
    )
    db.commit()
    db.refresh(schema)

    return {
        "id": schema.id,
        "name": schema.name,
        "description": schema.description,
        "version": schema.version,
        "is_active": schema.is_active,
        "fields": schema.fields,
        "created_at": schema.created_at,
        "updated_at": schema.updated_at,
        "message": "Metadata schema created successfully",
    }


@router.get(
    "/{schema_id}",
    dependencies=[Depends(require_permission("SCHEMA_READ"))],
)
def get_schema(
    schema_id: int,
    db: Session = Depends(get_db),
):
    schema = db.query(MetadataSchema).filter(MetadataSchema.id == schema_id).first()
    if not schema:
        raise HTTPException(status_code=404, detail="Metadata schema not found")

    return {
        "id": schema.id,
        "name": schema.name,
        "description": schema.description,
        "version": schema.version,
        "is_active": schema.is_active,
        "fields": schema.fields,
        "created_at": schema.created_at,
        "updated_at": schema.updated_at,
    }


@router.put(
    "/{schema_id}",
    dependencies=[Depends(require_permission("SCHEMA_WRITE"))],
)
def update_schema(
    schema_id: int,
    payload: MetadataSchemaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schema = db.query(MetadataSchema).filter(MetadataSchema.id == schema_id).first()
    if not schema:
        raise HTTPException(status_code=404, detail="Metadata schema not found")

    if payload.name is not None and payload.name.strip() != schema.name:
        existing = db.query(MetadataSchema).filter(
            MetadataSchema.name == payload.name.strip(),
            MetadataSchema.id != schema_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Metadata schema with name '{payload.name}' already exists",
            )
        schema.name = payload.name.strip()

    if payload.description is not None:
        schema.description = payload.description.strip() if payload.description else None

    if payload.version is not None:
        schema.version = payload.version

    if payload.is_active is not None:
        schema.is_active = payload.is_active

    if payload.fields is not None:
        names = [f.name for f in payload.fields]
        if len(names) != len(set(names)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Field names within a schema must be unique",
            )
        schema.fields = [f.model_dump() for f in payload.fields]

    create_audit_event(
        db=db,
        action="SCHEMA_UPDATE",
        user_id=current_user.id,
        resource_type="schema",
        resource_id=str(schema.id),
        success=True,
        details={"name": schema.name, "version": schema.version},
    )
    db.commit()
    db.refresh(schema)

    return {
        "id": schema.id,
        "name": schema.name,
        "description": schema.description,
        "version": schema.version,
        "is_active": schema.is_active,
        "fields": schema.fields,
        "updated_at": schema.updated_at,
        "message": "Metadata schema updated successfully",
    }


@router.delete(
    "/{schema_id}",
    dependencies=[Depends(require_permission("SCHEMA_WRITE"))],
)
def delete_schema(
    schema_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schema = db.query(MetadataSchema).filter(MetadataSchema.id == schema_id).first()
    if not schema:
        raise HTTPException(status_code=404, detail="Metadata schema not found")

    schema_name = schema.name
    db.delete(schema)

    create_audit_event(
        db=db,
        action="SCHEMA_DELETE",
        user_id=current_user.id,
        resource_type="schema",
        resource_id=str(schema_id),
        success=True,
        details={"name": schema_name},
    )
    db.commit()

    return {
        "id": schema_id,
        "message": f"Metadata schema '{schema_name}' deleted successfully",
    }


@router.post(
    "/{schema_id}/validate",
    dependencies=[Depends(require_permission("SCHEMA_READ"))],
)
def validate_metadata(
    schema_id: int,
    request: MetadataValidationRequest,
    db: Session = Depends(get_db),
):
    schema = db.query(MetadataSchema).filter(MetadataSchema.id == schema_id).first()
    if not schema:
        raise HTTPException(status_code=404, detail="Metadata schema not found")

    errors = validate_payload_against_schema(schema, request.metadata)
    return {
        "schema_id": schema.id,
        "schema_name": schema.name,
        "is_valid": len(errors) == 0,
        "errors": errors,
    }
