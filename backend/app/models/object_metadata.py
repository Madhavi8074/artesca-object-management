from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ObjectMetadata(Base):
    __tablename__ = "object_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)

    object_id: Mapped[int] = mapped_column(
        ForeignKey("objects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    classification: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    department: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )

    project: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )

    document_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    author: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    schema_id: Mapped[int | None] = mapped_column(
        ForeignKey("metadata_schemas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    custom_metadata: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
