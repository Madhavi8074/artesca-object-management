"""metadata schemas and jsonb indexing

Revision ID: b81a4d93e120
Revises: ef2d9fa291ae
Create Date: 2026-10-04 03:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b81a4d93e120'
down_revision: Union[str, Sequence[str], None] = 'ef2d9fa291ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create metadata_schemas table
    op.create_table(
        'metadata_schemas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='1.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('fields', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metadata_schemas_name'), 'metadata_schemas', ['name'], unique=True)

    # 2. Add schema_id to object_metadata
    op.add_column(
        'object_metadata',
        sa.Column('schema_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_object_metadata_schema_id',
        'object_metadata',
        'metadata_schemas',
        ['schema_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index(op.f('ix_object_metadata_schema_id'), 'object_metadata', ['schema_id'], unique=False)

    # 3. Create GIN index on custom_metadata if PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relname = 'ix_object_metadata_custom_metadata_gin'
                ) THEN
                    -- Convert column type to jsonb if it is json
                    ALTER TABLE object_metadata ALTER COLUMN custom_metadata TYPE jsonb USING custom_metadata::jsonb;
                    CREATE INDEX ix_object_metadata_custom_metadata_gin ON object_metadata USING gin (custom_metadata);
                END IF;
            END $$;
            """
        )

    # 4. Insert new atomic permissions and assign to ADMIN role
    permissions_to_add = [
        ('SCHEMA_READ', 'Read and list metadata schemas'),
        ('SCHEMA_WRITE', 'Create, update, and delete metadata schemas'),
        ('ROLE_ADMIN', 'Manage roles and permissions'),
        ('USER_ADMIN', 'Manage users and assign roles'),
    ]

    for name, desc in permissions_to_add:
        op.execute(
            f"""
            INSERT INTO permissions (name, description)
            VALUES ('{name}', '{desc}')
            ON CONFLICT (name) DO NOTHING;
            """
        )

    # Grant new permissions to the ADMIN role
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'ADMIN'
          AND p.name IN ('SCHEMA_READ', 'SCHEMA_WRITE', 'ROLE_ADMIN', 'USER_ADMIN')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
        """
    )

    # Also grant SCHEMA_READ to EDITOR role
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'EDITOR'
          AND p.name IN ('SCHEMA_READ')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP INDEX IF EXISTS ix_object_metadata_custom_metadata_gin;")

    op.drop_constraint('fk_object_metadata_schema_id', 'object_metadata', type_='foreignkey')
    op.drop_index(op.f('ix_object_metadata_schema_id'), table_name='object_metadata')
    op.drop_column('object_metadata', 'schema_id')

    op.drop_index(op.f('ix_metadata_schemas_name'), table_name='metadata_schemas')
    op.drop_table('metadata_schemas')
