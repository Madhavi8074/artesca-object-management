#!/usr/bin/env python3
"""
Initialize and Seed Database Schema & Default Roles/Users

Compatible with both PostgreSQL and SQLite.
Creates all tables and ensures default roles (ADMIN, EDITOR)
and default users (madhavi, editor) exist with correct permissions.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, SessionLocal
from app.models.base import Base
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.services.auth import password_hash


def init_database():
    print(f"Connecting to database: {engine.url.render_as_string(hide_password=True)}")
    
    # 1. Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables verified.")

    db = SessionLocal()
    try:
        # 2. Seed Permissions
        permissions_data = [
            ("OBJECT_UPLOAD", "Upload new objects to S3"),
            ("OBJECT_READ", "Read object metadata and list objects"),
            ("OBJECT_UPDATE", "Update object metadata and custom tags"),
            ("OBJECT_DOWNLOAD", "Download object payloads from S3"),
            ("OBJECT_DELETE", "Delete objects and metadata"),
            ("AUDIT_READ", "Read security and compliance audit logs"),
            ("SCHEMA_READ", "Read and list metadata schemas"),
            ("SCHEMA_WRITE", "Create, update, and delete metadata schemas"),
            ("ROLE_ADMIN", "Manage roles and permissions"),
            ("USER_ADMIN", "Manage users and assign roles"),
        ]

        perm_map = {}
        for code, desc in permissions_data:
            perm = db.query(Permission).filter(Permission.name == code).first()
            if not perm:
                perm = Permission(name=code, description=desc)
                db.add(perm)
                db.flush()
            perm_map[code] = perm

        # 3. Seed Roles
        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
        if not admin_role:
            admin_role = Role(name="ADMIN", description="Full administrative access")
            db.add(admin_role)
            db.flush()

        editor_role = db.query(Role).filter(Role.name == "EDITOR").first()
        if not editor_role:
            editor_role = Role(name="EDITOR", description="Editor role with read/write access")
            db.add(editor_role)
            db.flush()

        # 4. Map Permissions to Roles
        admin_perms = list(perm_map.values())
        editor_perms = [perm_map[c] for c in ("OBJECT_UPLOAD", "OBJECT_READ", "OBJECT_UPDATE", "OBJECT_DOWNLOAD", "SCHEMA_READ")]

        for p in admin_perms:
            exists = db.query(RolePermission).filter_by(role_id=admin_role.id, permission_id=p.id).first()
            if not exists:
                db.add(RolePermission(role_id=admin_role.id, permission_id=p.id))

        for p in editor_perms:
            exists = db.query(RolePermission).filter_by(role_id=editor_role.id, permission_id=p.id).first()
            if not exists:
                db.add(RolePermission(role_id=editor_role.id, permission_id=p.id))

        db.flush()

        # Seed initial metadata schemas if none exist
        from app.models.metadata_schema import MetadataSchema
        if db.query(MetadataSchema).count() == 0:
            db.add(
                MetadataSchema(
                    name="Enterprise Document Schema",
                    description="Standard enterprise document classification, retention, and department metadata",
                    version="1.0",
                    is_active=True,
                    fields=[
                        {"name": "retention_years", "label": "Retention Period (Years)", "type": "number", "required": True, "default_value": 7, "min_value": 1, "max_value": 100},
                        {"name": "confidentiality_level", "label": "Confidentiality Level", "type": "enum", "required": True, "options": ["Low", "Medium", "High", "Critical"], "default_value": "Medium"},
                        {"name": "compliance_standard", "label": "Compliance Standard", "type": "string", "required": False, "default_value": "ISO-27001"},
                        {"name": "is_reviewed", "label": "Security Reviewed", "type": "boolean", "required": False, "default_value": False},
                    ],
                )
            )
            db.flush()

        # 5. Seed Users
        # Admin: madhavi / Madhavi@123
        madhavi = db.query(User).filter(User.username == "madhavi").first()
        if not madhavi:
            madhavi = User(
                username="madhavi",
                email="madhavi@example.com",
                display_name="Madhavi",
                department="Engineering",
                is_active=True,
                password_hash=password_hash.hash("Artesca123"),
            )
            db.add(madhavi)
            db.flush()
            db.add(UserRole(user_id=madhavi.id, role_id=admin_role.id))

        # Editor: editor / Editor@123
        editor = db.query(User).filter(User.username == "editor").first()
        if not editor:
            editor = User(
                username="editor",
                email="editor@example.com",
                display_name="Editor User",
                department="Engineering",
                is_active=True,
                password_hash=password_hash.hash("Artesca123"),
            )
            db.add(editor)
            db.flush()
            db.add(UserRole(user_id=editor.id, role_id=editor_role.id))

        db.commit()
        print("✓ Default users and roles seeded successfully:")
        print("   - Admin:  madhavi / Artesca123")
        print("   - Editor: editor  / Artesca123")

    except Exception as exc:
        db.rollback()
        print(f"Error during database initialization: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
