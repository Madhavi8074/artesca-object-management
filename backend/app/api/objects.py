import json
from datetime import datetime
from typing import List, Optional
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel, Field

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.session import settings
from app.models.object import Object
from app.models.object_metadata import ObjectMetadata
from app.models.user import User
from app.schemas.object import ObjectUpdate
from app.services.audit import create_audit_event
from app.services.permissions import require_permission
from app.services.s3 import (
    s3_client,
    list_buckets as s3_list_buckets,
    create_folder as s3_create_folder,
    generate_presigned_download_url,
    generate_presigned_upload_url,
    ensure_bucket_exists,
)

router = APIRouter(
    prefix="/api/v1/objects",
    tags=["Objects"],
    dependencies=[Depends(get_current_user)],
)


class CreateFolderRequest(BaseModel):
    bucket: Optional[str] = None
    folder_name: str = Field(..., min_length=1, max_length=200)
    parent_prefix: Optional[str] = ""


class PresignedUploadRequest(BaseModel):
    bucket: Optional[str] = None
    object_key: str
    content_type: Optional[str] = "application/octet-stream"
    expires_in: Optional[int] = Field(default=3600, ge=60, le=604800)


# ============================================================
# BUCKET LISTING
# ============================================================

@router.get(
    "/buckets",
    dependencies=[Depends(require_permission("OBJECT_READ"))],
)
def list_available_buckets():
    """
    List S3 buckets accessible by configured credentials.
    """
    try:
        buckets = s3_list_buckets()
        return buckets
    except ClientError as exc:
        error = exc.response.get("Error", {})
        code = error.get("Code", "Unknown")

        if code in ("AccessDenied", "AllAccessDisabled"):
            raise HTTPException(
                status_code=403,
                detail="Configured S3 credentials cannot list buckets. Check IAM permissions.",
            ) from exc

        raise HTTPException(
            status_code=502,
            detail=f"S3 bucket listing failed: {code}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to S3 storage: {str(exc)}",
        ) from exc


# ============================================================
# FOLDER MANAGEMENT
# ============================================================

@router.post(
    "/folders",
    dependencies=[Depends(require_permission("OBJECT_UPLOAD"))],
)
def create_virtual_folder(
    request: CreateFolderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a directory/folder marker in S3 object storage and index it in the catalog.
    """
    target_bucket = (request.bucket or settings.s3_bucket).strip()
    clean_name = request.folder_name.strip().strip("/")
    if not clean_name:
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")

    prefix = (request.parent_prefix or "").strip().strip("/")
    folder_key = f"{prefix}/{clean_name}/" if prefix else f"{clean_name}/"

    # Check if folder already exists in DB
    existing = db.query(Object).filter(
        Object.bucket == target_bucket,
        Object.object_key == folder_key,
    ).first()

    if existing:
        return {
            "id": existing.id,
            "bucket": existing.bucket,
            "object_key": existing.object_key,
            "filename": existing.filename,
            "is_folder": True,
            "message": "Folder already exists",
        }

    try:
        # Create 0-byte directory marker in S3
        s3_create_folder(target_bucket, folder_key)

        folder_obj = Object(
            bucket=target_bucket,
            object_key=folder_key,
            filename=clean_name,
            content_type="application/x-directory",
            size_bytes=0,
            owner_id=current_user.id,
            status="ACTIVE",
        )
        db.add(folder_obj)
        db.flush()

        create_audit_event(
            db=db,
            action="FOLDER_CREATE",
            object_id=folder_obj.id,
            user_id=current_user.id,
            resource_type="folder",
            resource_id=folder_key,
            success=True,
            details={
                "bucket": target_bucket,
                "folder_key": folder_key,
            },
        )
        db.commit()
        db.refresh(folder_obj)

        return {
            "id": folder_obj.id,
            "bucket": folder_obj.bucket,
            "object_key": folder_obj.object_key,
            "filename": folder_obj.filename,
            "is_folder": True,
            "message": f"Folder '{clean_name}' created successfully",
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(exc)}")


# ============================================================
# PRESIGNED URLS & SHARE LINKS
# ============================================================

@router.get(
    "/{object_id}/share",
    dependencies=[Depends(require_permission("OBJECT_READ"))],
)
def generate_share_link(
    object_id: int,
    expires_in: int = Query(default=3600, ge=60, le=604800, description="Expiration in seconds (default 1 hour, max 7 days)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a secure, time-limited presigned share link for direct browser downloading.
    Never exposes S3 access keys or secret credentials to the client.
    """
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    try:
        presigned_url = generate_presigned_download_url(
            bucket=obj.bucket,
            key=obj.object_key,
            filename=obj.filename,
            expires_in=expires_in,
        )

        create_audit_event(
            db=db,
            action="OBJECT_SHARE",
            object_id=obj.id,
            user_id=current_user.id,
            resource_type="object",
            resource_id=str(obj.id),
            success=True,
            details={
                "bucket": obj.bucket,
                "object_key": obj.object_key,
                "filename": obj.filename,
                "expires_in": expires_in,
            },
        )
        db.commit()

        return {
            "object_id": obj.id,
            "filename": obj.filename,
            "share_url": presigned_url,
            "expires_in": expires_in,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate presigned share link: {str(exc)}",
        )


@router.get(
    "/{object_id}/presigned-download",
    dependencies=[Depends(require_permission("OBJECT_DOWNLOAD"))],
)
def get_presigned_download(
    object_id: int,
    expires_in: int = Query(default=3600, ge=60, le=86400),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a presigned download URL for direct client download.
    """
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    try:
        url = generate_presigned_download_url(
            bucket=obj.bucket,
            key=obj.object_key,
            filename=obj.filename,
            expires_in=expires_in,
        )
        return {"download_url": url, "expires_in": expires_in}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Presigned URL generation failed: {str(exc)}")


@router.post(
    "/presigned-upload",
    dependencies=[Depends(require_permission("OBJECT_UPLOAD"))],
)
def get_presigned_upload(
    request: PresignedUploadRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a presigned PUT URL allowing clients to upload directly to S3.
    """
    target_bucket = (request.bucket or settings.s3_bucket).strip()
    try:
        res = generate_presigned_upload_url(
            bucket=target_bucket,
            key=request.object_key.strip(),
            content_type=request.content_type or "application/octet-stream",
            expires_in=request.expires_in or 3600,
        )
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(exc)}")


# ============================================================
# UPLOAD OBJECT WITH METADATA & SCHEMA VALIDATION
# ============================================================

@router.post(
    "/upload",
    dependencies=[Depends(require_permission("OBJECT_UPLOAD"))],
)
def upload_object(
    file: UploadFile = File(...),
    bucket: str = Form(default=settings.s3_bucket),
    object_key: str = Form(...),
    department: Optional[str] = Form(default=None),
    project: Optional[str] = Form(default=None),
    classification: Optional[str] = Form(default=None),
    document_type: Optional[str] = Form(default=None),
    author: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    schema_id: Optional[int] = Form(default=None),
    custom_metadata: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parsed_custom_metadata = None
    if custom_metadata:
        try:
            parsed_custom_metadata = json.loads(custom_metadata)
            if not isinstance(parsed_custom_metadata, dict):
                raise ValueError("custom_metadata must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid custom_metadata JSON: {exc}",
            )

    clean_key = object_key.strip()
    clean_bucket = bucket.strip()

    # Ensure bucket exists
    ensure_bucket_exists(clean_bucket)

    existing_object = (
        db.query(Object)
        .filter(
            Object.bucket == clean_bucket,
            Object.object_key == clean_key,
        )
        .first()
    )

    if existing_object:
        raise HTTPException(
            status_code=409,
            detail=f"Object with key '{clean_key}' already exists in bucket '{clean_bucket}'",
        )

    try:
        file_content = file.file.read()

        # Upload file to S3-compatible storage
        s3_client.put_object(
            Bucket=clean_bucket,
            Key=clean_key,
            Body=file_content,
            ContentType=file.content_type or "application/octet-stream",
        )

        obj = Object(
            bucket=clean_bucket,
            object_key=clean_key,
            filename=file.filename or clean_key.split("/")[-1],
            content_type=file.content_type,
            size_bytes=len(file_content),
            owner_id=current_user.id,
            status="ACTIVE",
        )

        db.add(obj)
        db.flush()

        metadata = ObjectMetadata(
            object_id=obj.id,
            classification=classification,
            department=department,
            project=project,
            document_type=document_type,
            author=author,
            description=description,
            schema_id=schema_id,
            custom_metadata=parsed_custom_metadata,
        )

        db.add(metadata)

        create_audit_event(
            db=db,
            action="OBJECT_UPLOAD",
            object_id=obj.id,
            user_id=current_user.id,
            resource_type="object",
            resource_id=str(obj.id),
            success=True,
            details={
                "bucket": clean_bucket,
                "object_key": clean_key,
                "filename": file.filename,
                "size_bytes": len(file_content),
                "schema_id": schema_id,
            },
        )

        db.commit()
        db.refresh(obj)
        db.refresh(metadata)

        return {
            "id": obj.id,
            "bucket": obj.bucket,
            "object_key": obj.object_key,
            "filename": obj.filename,
            "content_type": obj.content_type,
            "size_bytes": obj.size_bytes,
            "status": obj.status,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "metadata": {
                "classification": metadata.classification,
                "department": metadata.department,
                "project": metadata.project,
                "document_type": metadata.document_type,
                "author": metadata.author,
                "description": metadata.description,
                "schema_id": metadata.schema_id,
                "custom_metadata": metadata.custom_metadata,
            },
            "message": "Object uploaded and indexed successfully",
        }

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        try:
            s3_client.delete_object(
                Bucket=clean_bucket,
                Key=clean_key,
            )
        except Exception:
            pass

        create_audit_event(
            db=db,
            action="OBJECT_UPLOAD",
            user_id=current_user.id,
            resource_type="object",
            resource_id=clean_key,
            success=False,
            error_code="UPLOAD_FAILED",
            details={
                "bucket": clean_bucket,
                "object_key": clean_key,
                "error": str(exc),
            },
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(exc)}",
        )


# ============================================================
# LIST OBJECTS (WITH PREFIX / FOLDER FILTERING)
# ============================================================

@router.get(
    "/",
    dependencies=[Depends(require_permission("OBJECT_READ"))],
)
def list_objects(
    bucket: Optional[str] = Query(default=None),
    prefix: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default="ACTIVE"),
    db: Session = Depends(get_db),
):
    query = db.query(Object)

    if status_filter:
        query = query.filter(Object.status == status_filter)

    if bucket:
        query = query.filter(Object.bucket == bucket)

    if prefix:
        clean_prefix = prefix.strip()
        query = query.filter(Object.object_key.startswith(clean_prefix))

    query = query.order_by(Object.id.desc())
    objects = query.all()

    return [
        {
            "id": obj.id,
            "bucket": obj.bucket,
            "object_key": obj.object_key,
            "filename": obj.filename,
            "content_type": obj.content_type,
            "size_bytes": obj.size_bytes,
            "etag": obj.etag,
            "version_id": obj.version_id,
            "status": obj.status,
            "is_folder": (obj.content_type == "application/x-directory" or obj.object_key.endswith("/")),
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        for obj in objects
    ]


# ============================================================
# GET SINGLE OBJECT
# ============================================================

@router.get(
    "/{object_id}",
    dependencies=[Depends(require_permission("OBJECT_READ"))],
)
def get_object(
    object_id: int,
    db: Session = Depends(get_db),
):
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    metadata = db.query(ObjectMetadata).filter(ObjectMetadata.object_id == obj.id).first()

    return {
        "id": obj.id,
        "bucket": obj.bucket,
        "object_key": obj.object_key,
        "filename": obj.filename,
        "content_type": obj.content_type,
        "size_bytes": obj.size_bytes,
        "etag": obj.etag,
        "version_id": obj.version_id,
        "status": obj.status,
        "is_folder": (obj.content_type == "application/x-directory" or obj.object_key.endswith("/")),
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
        "metadata": (
            {
                "classification": metadata.classification,
                "department": metadata.department,
                "project": metadata.project,
                "document_type": metadata.document_type,
                "author": metadata.author,
                "description": metadata.description,
                "schema_id": metadata.schema_id,
                "custom_metadata": metadata.custom_metadata,
            }
            if metadata
            else None
        ),
    }


# ============================================================
# DOWNLOAD OBJECT (DIRECT STREAMING)
# ============================================================

@router.get(
    "/{object_id}/download",
    dependencies=[Depends(require_permission("OBJECT_DOWNLOAD"))],
)
def download_object(
    object_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    try:
        s3_response = s3_client.get_object(
            Bucket=obj.bucket,
            Key=obj.object_key,
        )

        create_audit_event(
            db=db,
            action="OBJECT_DOWNLOAD",
            object_id=obj.id,
            user_id=current_user.id,
            resource_type="object",
            resource_id=str(obj.id),
            success=True,
            details={
                "bucket": obj.bucket,
                "object_key": obj.object_key,
                "filename": obj.filename,
            },
        )
        db.commit()

        return StreamingResponse(
            s3_response["Body"].iter_chunks(),
            media_type=obj.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{obj.filename}"',
            },
        )
    except Exception as exc:
        create_audit_event(
            db=db,
            action="OBJECT_DOWNLOAD",
            object_id=obj.id,
            user_id=current_user.id,
            resource_type="object",
            resource_id=str(obj.id),
            success=False,
            error_code="DOWNLOAD_FAILED",
            details={"error": str(exc)},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(exc)}",
        )


# ============================================================
# DELETE OBJECT
# ============================================================

@router.delete(
    "/{object_id}",
    dependencies=[Depends(require_permission("OBJECT_DELETE"))],
)
def delete_object(
    object_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    object_id_val = obj.id
    bucket = obj.bucket
    object_key = obj.object_key
    filename = obj.filename

    try:
        try:
            s3_client.delete_object(Bucket=bucket, Key=object_key)
        except Exception:
            pass

        db.query(ObjectMetadata).filter(ObjectMetadata.object_id == object_id_val).delete()

        create_audit_event(
            db=db,
            action="OBJECT_DELETE",
            object_id=object_id_val,
            user_id=current_user.id,
            resource_type="object",
            resource_id=str(object_id_val),
            success=True,
            details={"bucket": bucket, "object_key": object_key, "filename": filename},
        )

        db.delete(obj)
        db.commit()

        return {
            "id": object_id_val,
            "message": "Object and metadata deleted successfully",
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(exc)}")


# ============================================================
# UPDATE OBJECT & METADATA
# ============================================================

@router.put(
    "/{object_id}",
    dependencies=[Depends(require_permission("OBJECT_UPDATE"))],
)
def update_object(
    object_id: int,
    payload: ObjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = db.query(Object).filter(Object.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    metadata = db.query(ObjectMetadata).filter(ObjectMetadata.object_id == obj.id).first()

    try:
        updated_fields = {}

        if payload.filename is not None:
            obj.filename = payload.filename.strip()
            updated_fields["filename"] = obj.filename

        if payload.content_type is not None:
            obj.content_type = payload.content_type.strip()
            updated_fields["content_type"] = obj.content_type

        if metadata is None:
            metadata = ObjectMetadata(object_id=obj.id)
            db.add(metadata)
            db.flush()

        if payload.classification is not None:
            metadata.classification = payload.classification
            updated_fields["classification"] = payload.classification

        if payload.department is not None:
            metadata.department = payload.department
            updated_fields["department"] = payload.department

        if payload.project is not None:
            metadata.project = payload.project
            updated_fields["project"] = payload.project

        if payload.document_type is not None:
            metadata.document_type = payload.document_type
            updated_fields["document_type"] = payload.document_type

        if payload.author is not None:
            metadata.author = payload.author
            updated_fields["author"] = payload.author

        if payload.description is not None:
            metadata.description = payload.description
            updated_fields["description"] = payload.description

        if payload.schema_id is not None:
            metadata.schema_id = payload.schema_id
            updated_fields["schema_id"] = payload.schema_id

        if payload.custom_metadata is not None:
            metadata.custom_metadata = payload.custom_metadata
            updated_fields["custom_metadata"] = payload.custom_metadata

        create_audit_event(
            db=db,
            action="OBJECT_METADATA_UPDATE",
            object_id=obj.id,
            user_id=current_user.id,
            resource_type="object",
            resource_id=str(obj.id),
            success=True,
            details={
                "filename": obj.filename,
                "bucket": obj.bucket,
                "object_key": obj.object_key,
                "updated_fields": updated_fields,
            },
        )
        db.commit()
        db.refresh(obj)
        db.refresh(metadata)

        return {
            "id": obj.id,
            "bucket": obj.bucket,
            "object_key": obj.object_key,
            "filename": obj.filename,
            "content_type": obj.content_type,
            "size_bytes": obj.size_bytes,
            "status": obj.status,
            "metadata": {
                "classification": metadata.classification,
                "department": metadata.department,
                "project": metadata.project,
                "document_type": metadata.document_type,
                "author": metadata.author,
                "description": metadata.description,
                "schema_id": metadata.schema_id,
                "custom_metadata": metadata.custom_metadata,
            },
            "message": "Object metadata updated successfully",
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(exc)}")
