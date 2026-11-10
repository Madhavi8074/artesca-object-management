from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ObjectMetadataCreate(BaseModel):
    classification: Optional[str] = None
    department: Optional[str] = None
    project: Optional[str] = None
    document_type: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    schema_id: Optional[int] = None
    custom_metadata: Optional[dict[str, Any]] = None


class ObjectCreate(BaseModel):
    bucket: str = Field(min_length=1, max_length=255)
    object_key: str = Field(min_length=1)
    filename: str = Field(min_length=1, max_length=500)
    content_type: Optional[str] = Field(default=None, max_length=255)
    size_bytes: int = Field(ge=0)
    etag: Optional[str] = Field(default=None, max_length=255)
    version_id: Optional[str] = Field(default=None, max_length=255)
    owner_id: Optional[int] = None
    metadata: Optional[ObjectMetadataCreate] = None


class ObjectUpdate(BaseModel):
    filename: Optional[str] = Field(default=None, min_length=1, max_length=500)
    content_type: Optional[str] = Field(default=None, max_length=255)
    classification: Optional[str] = None
    department: Optional[str] = None
    project: Optional[str] = None
    document_type: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    schema_id: Optional[int] = None
    custom_metadata: Optional[dict[str, Any]] = None
