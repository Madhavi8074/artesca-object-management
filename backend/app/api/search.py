import math
import re
from typing import Any, List, Optional, Union
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import (
    Float,
    and_,
    cast,
    func,
    not_,
    or_,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.object import Object
from app.models.object_metadata import ObjectMetadata
from app.services.permissions import require_permission

router = APIRouter(
    prefix="/api/v1/search",
    tags=["Search"],
    dependencies=[Depends(get_current_user)],
)


# ============================================================
# QUERY BUILDER AST PYDANTIC MODELS
# ============================================================

class QueryRule(BaseModel):
    field: str
    operator: str  # equals, not_equals, contains, not_contains, starts_with, ends_with, regex, gt, gte, lt, lte, between, exists, not_exists
    value: Optional[Any] = None


class QueryGroup(BaseModel):
    combinator: str = "AND"  # "AND", "OR", "NOT"
    rules: List[Union[QueryRule, "QueryGroup"]] = Field(default_factory=list)


QueryGroup.model_rebuild()


class AdvancedQueryRequest(BaseModel):
    root: QueryGroup


# ============================================================
# FIELD MAPPING HELPER
# ============================================================

COLUMN_MAP = {
    "filename": Object.filename,
    "original_name": Object.filename,
    "object_key": Object.object_key,
    "content_type": Object.content_type,
    "bucket": Object.bucket,
    "size_bytes": Object.size_bytes,
    "status": Object.status,
    "created_at": Object.created_at,
    "updated_at": Object.updated_at,
    "classification": ObjectMetadata.classification,
    "department": ObjectMetadata.department,
    "project": ObjectMetadata.project,
    "document_type": ObjectMetadata.document_type,
    "author": ObjectMetadata.author,
    "description": ObjectMetadata.description,
    "schema_id": ObjectMetadata.schema_id,
}


def build_rule_expression(rule: QueryRule, is_postgres: bool):
    field = rule.field.strip()
    op = rule.operator.strip().lower()
    val = rule.value

    # Check if standard column
    if field in COLUMN_MAP:
        col = COLUMN_MAP[field]
        if hasattr(col, "type"):
            try:
                py_type = getattr(col.type, "python_type", None)
                if py_type is int and val is not None and not isinstance(val, (list, tuple)):
                    val = int(val)
                elif py_type is float and val is not None and not isinstance(val, (list, tuple)):
                    val = float(val)
            except Exception:
                pass

        if op == "equals":
            return col == val
        elif op == "not_equals":
            return col != val
        elif op == "contains":
            return col.ilike(f"%{val}%")
        elif op == "not_contains":
            return not_(col.ilike(f"%{val}%"))
        elif op == "starts_with":
            return col.ilike(f"{val}%")
        elif op == "ends_with":
            return col.ilike(f"%{val}")
        elif op == "regex":
            if is_postgres:
                return col.op("~*")(str(val))
            else:
                return col.ilike(f"%{val}%")
        elif op in ("gt", ">"):
            return col > val
        elif op in ("gte", ">="):
            return col >= val
        elif op in ("lt", "<"):
            return col < val
        elif op in ("lte", "<="):
            return col <= val
        elif op == "between":
            if isinstance(val, (list, tuple)) and len(val) == 2:
                return col.between(val[0], val[1])
            return None
        elif op == "is_null":
            return col.is_(None)
        elif op == "is_not_null":
            return col.is_not(None)
        elif op == "in":
            if isinstance(val, (list, tuple)):
                return col.in_(val)
            return col == val
        elif op == "not_in":
            if isinstance(val, (list, tuple)):
                return col.not_in(val)
            return col != val
        return None

    # Otherwise, field is a custom JSONB attribute (e.g. "custom_metadata.project_code", "custom.tier", or "project_code")
    if field.startswith("custom_metadata."):
        json_key = field[len("custom_metadata."):]
    elif field.startswith("custom."):
        json_key = field[len("custom."):]
    elif field.startswith("metadata."):
        json_key = field[len("metadata."):]
    else:
        json_key = field

    if is_postgres:
        json_col = cast(ObjectMetadata.custom_metadata, JSONB)

        if op in ("exists", "is_not_null"):
            return json_col.has_key(json_key)
        elif op in ("not_exists", "is_null"):
            return not_(json_col.has_key(json_key))
        elif op == "equals":
            return json_col[json_key].astext == str(val)
        elif op == "not_equals":
            return or_(not_(json_col.has_key(json_key)), json_col[json_key].astext != str(val))
        elif op == "contains":
            return json_col[json_key].astext.ilike(f"%{val}%")
        elif op == "not_contains":
            return or_(not_(json_col.has_key(json_key)), not_(json_col[json_key].astext.ilike(f"%{val}%")))
        elif op == "starts_with":
            return json_col[json_key].astext.ilike(f"{val}%")
        elif op == "ends_with":
            return json_col[json_key].astext.ilike(f"%{val}")
        elif op in ("gt", ">"):
            try:
                num = float(val)
                return and_(json_col.has_key(json_key), cast(json_col[json_key].astext, Float) > num)
            except (ValueError, TypeError):
                return json_col[json_key].astext > str(val)
        elif op in ("gte", ">="):
            try:
                num = float(val)
                return and_(json_col.has_key(json_key), cast(json_col[json_key].astext, Float) >= num)
            except (ValueError, TypeError):
                return json_col[json_key].astext >= str(val)
        elif op in ("lt", "<"):
            try:
                num = float(val)
                return and_(json_col.has_key(json_key), cast(json_col[json_key].astext, Float) < num)
            except (ValueError, TypeError):
                return json_col[json_key].astext < str(val)
        elif op in ("lte", "<="):
            try:
                num = float(val)
                return and_(json_col.has_key(json_key), cast(json_col[json_key].astext, Float) <= num)
            except (ValueError, TypeError):
                return json_col[json_key].astext <= str(val)
        elif op == "between":
            if isinstance(val, (list, tuple)) and len(val) == 2:
                try:
                    n1, n2 = float(val[0]), float(val[1])
                    return and_(
                        json_col.has_key(json_key),
                        cast(json_col[json_key].astext, Float).between(n1, n2),
                    )
                except (ValueError, TypeError):
                    return json_col[json_key].astext.between(str(val[0]), str(val[1]))
            return None
        elif op == "json_contains":
            # Native JSONB containment: @>
            return json_col.contains({json_key: val})

    else:
        # Cross-dialect fallback for SQLite
        path = f"$.{json_key}"
        json_ext = func.json_extract(ObjectMetadata.custom_metadata, path)

        if op in ("exists", "is_not_null"):
            return json_ext.is_not(None)
        elif op in ("not_exists", "is_null"):
            return json_ext.is_(None)
        elif op == "equals":
            return json_ext == val
        elif op == "not_equals":
            return json_ext != val
        elif op == "contains":
            return json_ext.ilike(f"%{val}%")
        elif op == "not_contains":
            return not_(json_ext.ilike(f"%{val}%"))
        elif op in ("gt", ">"):
            return json_ext > val
        elif op in ("gte", ">="):
            return json_ext >= val
        elif op in ("lt", "<"):
            return json_ext < val
        elif op in ("lte", "<="):
            return json_ext <= val

    return None


def compile_group(group: QueryGroup, is_postgres: bool):
    """
    Recursively compile an AST QueryGroup into SQLAlchemy binary expressions.
    """
    exprs = []
    for item in group.rules:
        if isinstance(item, QueryGroup):
            sub_expr = compile_group(item, is_postgres)
            if sub_expr is not None:
                exprs.append(sub_expr)
        elif isinstance(item, QueryRule):
            rule_expr = build_rule_expression(item, is_postgres)
            if rule_expr is not None:
                exprs.append(rule_expr)

    if not exprs:
        return None

    comb = group.combinator.upper()
    if comb == "OR":
        return or_(*exprs)
    elif comb == "NOT":
        return not_(and_(*exprs))
    else:  # default AND
        return and_(*exprs)


def format_search_results(rows):
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
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "metadata": {
                "classification": metadata.classification if metadata else None,
                "department": metadata.department if metadata else None,
                "project": metadata.project if metadata else None,
                "document_type": metadata.document_type if metadata else None,
                "author": metadata.author if metadata else None,
                "description": metadata.description if metadata else None,
                "schema_id": metadata.schema_id if metadata else None,
                "custom_metadata": metadata.custom_metadata if metadata else None,
            },
        }
        for obj, metadata in rows
    ]


# ============================================================
# ENDPOINTS
# ============================================================

@router.post(
    "/query",
    dependencies=[Depends(require_permission("OBJECT_READ"))],
)
def visual_query_search(
    request: AdvancedQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Visual Query Builder search with recursive AND/OR/NOT condition groups
    and native PostgreSQL JSONB operators.
    """
    is_postgres = (db.bind.dialect.name == "postgresql") if db.bind else True

    base_query = (
        db.query(Object, ObjectMetadata)
        .outerjoin(ObjectMetadata, ObjectMetadata.object_id == Object.id)
    )

    filter_expr = compile_group(request.root, is_postgres)
    if filter_expr is not None:
        base_query = base_query.filter(filter_expr)

    base_query = base_query.order_by(Object.id.desc())
    rows = base_query.all()
    return format_search_results(rows)


@router.get(
    "/objects",
    dependencies=[Depends(require_permission("OBJECT_READ"))],
)
def search_objects(
    filename: Optional[str] = Query(default=None),
    object_key: Optional[str] = Query(default=None),
    object_key_regex: Optional[str] = Query(default=None),
    content_type: Optional[str] = Query(default=None),
    bucket: Optional[str] = Query(default=None),
    min_size: Optional[int] = Query(default=None, ge=0),
    max_size: Optional[int] = Query(default=None, ge=0),
    size_gt: Optional[int] = Query(default=None, ge=0),
    size_lt: Optional[int] = Query(default=None, ge=0),
    classification: Optional[str] = Query(default=None),
    department: Optional[str] = Query(default=None),
    project: Optional[str] = Query(default=None),
    document_type: Optional[str] = Query(default=None),
    author: Optional[str] = Query(default=None),
    description: Optional[str] = Query(default=None),
    custom_key: Optional[str] = Query(default=None),
    custom_value: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Multi-criteria search enhanced with PostgreSQL JSONB indexing.
    """
    query = (
        db.query(Object, ObjectMetadata)
        .outerjoin(
            ObjectMetadata,
            ObjectMetadata.object_id == Object.id,
        )
    )

    filters = []

    if filename:
        filters.append(Object.filename.ilike(f"%{filename}%"))

    if object_key:
        filters.append(Object.object_key.ilike(f"%{object_key}%"))

    if object_key_regex:
        is_postgres = (db.bind.dialect.name == "postgresql") if db.bind else True
        if is_postgres:
            filters.append(Object.object_key.op("~*")(object_key_regex))
        else:
            filters.append(Object.object_key.ilike(f"%{object_key_regex}%"))

    if content_type:
        filters.append(Object.content_type.ilike(f"%{content_type}%"))

    if bucket:
        filters.append(Object.bucket.ilike(f"%{bucket}%"))

    if min_size is not None:
        filters.append(Object.size_bytes >= min_size)

    if max_size is not None:
        filters.append(Object.size_bytes <= max_size)

    if size_gt is not None:
        filters.append(Object.size_bytes > size_gt)

    if size_lt is not None:
        filters.append(Object.size_bytes < size_lt)

    if classification:
        filters.append(ObjectMetadata.classification.ilike(f"%{classification}%"))

    if department:
        filters.append(ObjectMetadata.department.ilike(f"%{department}%"))

    if project:
        filters.append(ObjectMetadata.project.ilike(f"%{project}%"))

    if document_type:
        filters.append(ObjectMetadata.document_type.ilike(f"%{document_type}%"))

    if author:
        filters.append(ObjectMetadata.author.ilike(f"%{author}%"))

    if description:
        filters.append(ObjectMetadata.description.ilike(f"%{description}%"))

    if custom_key:
        dialect_name = db.bind.dialect.name if db.bind else "postgresql"
        if dialect_name == "postgresql":
            json_metadata = cast(ObjectMetadata.custom_metadata, JSONB)
            filters.append(json_metadata.has_key(custom_key))

            if custom_value:
                filters.append(
                    json_metadata[custom_key].astext.ilike(f"%{custom_value}%")
                )
        else:
            path = f"$.{custom_key}"
            filters.append(func.json_extract(ObjectMetadata.custom_metadata, path).is_not(None))
            if custom_value:
                filters.append(
                    func.json_extract(ObjectMetadata.custom_metadata, path).ilike(f"%{custom_value}%")
                )

    if filters:
        query = query.filter(and_(*filters))

    query = query.order_by(Object.id.desc())
    rows = query.all()
    return format_search_results(rows)
