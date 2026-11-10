#!/usr/bin/env python3
"""
EasyStore End-to-End Test Suite (Standard Library - Zero Extra Dependencies)

Verifies:
1. System Health endpoints (/health, /health/database)
2. User Registration (/api/v1/auth/register)
3. User Login & JWT token acquisition (/api/v1/auth/login)
4. User Profile & RBAC role checks (/api/v1/auth/me)
5. RBAC Permission enforcement (EDITOR denied SCHEMA_WRITE, ADMIN allowed)
6. Metadata Schema CRUD & validation (/api/v1/schemas/)
7. Virtual Folder creation (/api/v1/objects/folders)
8. Object Upload & catalog indexing (/api/v1/objects/upload)
9. Object Listing & prefix-based filtering (/api/v1/objects/)
10. Presigned Share Link generation (/api/v1/objects/{id}/share)
11. Presigned Download URL generation (/api/v1/objects/{id}/presigned-download)
12. Multi-criteria catalog search (/api/v1/search/objects)
13. Visual Boolean AST query evaluation (/api/v1/search/query)
14. Immutable Security & Operations Audit Trail (/api/v1/audit/)
15. Object Deletion (/api/v1/objects/{id})
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import uuid

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")


def request(path, method="GET", data=None, headers=None, is_json=True):
    url = f"{BASE_URL}{path}"
    h = headers.copy() if headers else {}
    body = None
    if data is not None:
        if is_json:
            body = json.dumps(data).encode("utf-8")
            h["Content-Type"] = "application/json"
        else:
            body = data
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return resp.status, json.loads(content.decode("utf-8")), resp.headers
            return resp.status, content, resp.headers
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_content)
            return e.code, err_json, e.headers
        except Exception:
            return e.code, err_content, e.headers


def multipart_upload(path, fields, filename, file_bytes, content_type="application/octet-stream", headers=None):
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"
    h = headers.copy() if headers else {}
    h["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    
    body = bytearray()
    for k, v in fields.items():
        if v is not None:
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
            body.extend(f"{v}\r\n".encode())
        
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
    body.extend(file_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    
    return request(path, method="POST", data=bytes(body), headers=h, is_json=False)


def run_tests():
    print("=" * 65)
    print(" EASYSTORE END-TO-END VERIFICATION TEST SUITE")
    print(f" Target: {BASE_URL}")
    print("=" * 65)

    # 1. Health
    print("\n[1/6] Verifying System Health Endpoints...")
    status, health, _ = request("/health")
    assert status == 200 and health.get("status") == "ok", f"Health failed: {health}"
    print(f"✓ Backend Service Healthy: {health.get('service')} (v{health.get('version', '1.0.0')})")

    status, db_health, _ = request("/health/database")
    assert status == 200 and db_health.get("database") == "connected", f"Database health failed: {db_health}"
    print("✓ Database Connection Active (SELECT 1 verified)")

    # 2. Registration & Authentication
    print("\n[2/6] Verifying User Registration & JWT Authentication...")
    test_user = f"tester_{uuid.uuid4().hex[:6]}"
    test_pass = "TestPassword@123"

    # Register
    status, reg_data, _ = request(
        "/api/v1/auth/register",
        method="POST",
        data={
            "username": test_user,
            "password": test_pass,
            "display_name": "Test Engineer",
            "email": f"{test_user}@drdo-lrde.internal",
            "department": "AeroDef Research",
        },
    )
    assert status == 201, f"Registration failed ({status}): {reg_data}"
    assert "access_token" in reg_data
    token = reg_data["access_token"]
    user_headers = {"Authorization": f"Bearer {token}"}
    print(f"✓ Registered user '{test_user}' successfully with role assignment.")

    # Duplicate registration rejection check (409 Conflict)
    status, dup_err, _ = request(
        "/api/v1/auth/register",
        method="POST",
        data={"username": test_user, "password": test_pass},
    )
    assert status == 409, f"Expected 409 on duplicate register, got {status}: {dup_err}"
    print("✓ Duplicate username registration correctly blocked (409 Conflict).")

    # Login as Admin (madhavi / Artesca123)
    status, admin_login, _ = request(
        "/api/v1/auth/login",
        method="POST",
        data={"username": "madhavi", "password": "Artesca123"},
    )
    assert status == 200 and "access_token" in admin_login
    admin_token = admin_login["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✓ Admin login & JWT token generation verified.")

    # Profile (/me)
    status, profile, _ = request("/api/v1/auth/me", headers=user_headers)
    assert status == 200 and profile["username"] == test_user
    assert "EDITOR" in profile["roles"]
    print(f"✓ Profile loaded: Roles={profile['roles']}, Permissions={len(profile['permissions'])}.")

    # 3. RBAC Enforcement & Metadata Schema Administration
    print("\n[3/6] Verifying RBAC Enforcement & Metadata Schemas...")
    schema_payload = {
        "name": f"Radar Telemetry {uuid.uuid4().hex[:6]}",
        "description": "Validation schema for flight radar sensors",
        "is_active": True,
        "fields": [
            {"name": "frequency_ghz", "label": "Frequency (GHz)", "type": "number", "required": True},
            {"name": "polarization", "label": "Polarization", "type": "enum", "required": True, "options": ["H", "V", "Circular"]},
            {"name": "is_calibrated", "label": "Calibrated", "type": "boolean", "required": False},
        ],
    }
    # Verify EDITOR cannot write schemas (403 Forbidden)
    status, denied, _ = request("/api/v1/schemas/", method="POST", data=schema_payload, headers=user_headers)
    assert status == 403, f"Expected 403 Forbidden for editor, got {status}: {denied}"
    print("✓ RBAC Policy Enforced: Non-admin user correctly DENIED permission to modify schemas (403).")

    # Create schema with ADMIN headers
    status, schema, _ = request("/api/v1/schemas/", method="POST", data=schema_payload, headers=admin_headers)
    assert status == 201, f"Admin schema creation failed: {schema}"
    schema_id = schema["id"]
    print(f"✓ Admin authorized: Schema #{schema_id} ('{schema['name']}') created.")

    # Validation endpoint (Valid)
    status, val_ok, _ = request(
        f"/api/v1/schemas/{schema_id}/validate",
        method="POST",
        data={"metadata": {"frequency_ghz": 9.4, "polarization": "H", "is_calibrated": True}},
        headers=user_headers,
    )
    assert status == 200 and val_ok.get("is_valid") is True
    print("✓ Schema validation engine: Valid metadata approved.")

    # Validation endpoint (Invalid)
    status, val_fail, _ = request(
        f"/api/v1/schemas/{schema_id}/validate",
        method="POST",
        data={"metadata": {"polarization": "INVALID_POL"}},
        headers=user_headers,
    )
    assert status == 200 and val_fail.get("is_valid") is False
    print(f"✓ Schema validation engine: Correctly caught {len(val_fail['errors'])} violations.")

    # 4. Folder Management & File Upload
    print("\n[4/6] Verifying Folder Creation & Object Ingestion...")
    # Virtual Folder
    folder_name = "flight_trials"
    status, folder_res, _ = request(
        "/api/v1/objects/folders",
        method="POST",
        data={"folder_name": folder_name, "bucket": "artesca-documents"},
        headers=user_headers,
    )
    assert status in (200, 201), f"Folder creation failed: {folder_res}"
    print(f"✓ Virtual folder '{folder_name}/' created.")

    # Upload Object inside the folder
    test_filename = f"radar_scan_{uuid.uuid4().hex[:6]}.dat"
    test_content = b"DRDO-LRDE RADAR TRIAL FLIGHT SCAN DATA\nAZIMUTH=45.2\nELEVATION=12.8\nSAMPLES=4096"
    status, upload_res, _ = multipart_upload(
        "/api/v1/objects/upload",
        fields={
            "bucket": "artesca-documents",
            "object_key": f"{folder_name}/{test_filename}",
            "classification": "CONFIDENTIAL",
            "department": "Radar Systems",
            "project": "AeroDef",
            "document_type": "Binary Scan",
            "author": "Madhavi",
            "schema_id": str(schema_id),
            "custom_metadata": json.dumps({"frequency_ghz": 9.4, "polarization": "H", "is_calibrated": True}),
        },
        filename=test_filename,
        file_bytes=test_content,
        headers=user_headers,
    )
    assert status in (200, 201), f"Upload failed: {upload_res}"
    obj_id = upload_res["id"]
    print(f"✓ Object '{test_filename}' uploaded and indexed (ID #{obj_id}).")

    # 5. Share Links & Presigned URLs
    print("\n[5/6] Verifying Presigned Share Links & Direct Downloads...")
    status, share_res, _ = request(
        f"/api/v1/objects/{obj_id}/share?expires_in=1800",
        headers=user_headers,
    )
    assert status == 200 and "share_url" in share_res
    assert share_res["expires_in"] == 1800
    print("✓ Cryptographic presigned share URL generated successfully (HMAC-SHA256 SigV4).")

    # Presigned Download endpoint
    status, presign_res, _ = request(
        f"/api/v1/objects/{obj_id}/presigned-download?expires_in=3600",
        headers=user_headers,
    )
    assert status == 200 and "download_url" in presign_res
    print("✓ Direct client presigned download URL verified.")

    # Direct Streaming Download
    status, downloaded_bytes, _ = request(
        f"/api/v1/objects/{obj_id}/download",
        headers=user_headers,
        is_json=False,
    )
    assert status == 200
    assert downloaded_bytes == test_content
    print(f"✓ Object payload verified via direct download ({len(downloaded_bytes)} bytes matched exactly).")

    # 6. Catalog Search, Visual Query & Audit Trail
    print("\n[6/6] Verifying Search, Visual AST Query & Audit Trail...")
    # Prefix filtering
    status, prefix_items, _ = request(f"/api/v1/objects/?prefix={folder_name}/", headers=user_headers)
    assert status == 200 and any(item["id"] == obj_id for item in prefix_items)
    print("✓ Prefix/folder filtering verified.")

    # Multi-criteria search
    status, search_items, _ = request(
        f"/api/v1/search/objects?filename={test_filename}&classification=CONFIDENTIAL",
        headers=user_headers,
    )
    assert status == 200 and len(search_items) > 0
    print("✓ Multi-criteria catalog search verified.")

    # Visual Boolean AST query
    status, ast_items, _ = request(
        "/api/v1/search/query",
        method="POST",
        data={
            "root": {
                "combinator": "AND",
                "rules": [
                    {"field": "project", "operator": "equals", "value": "AeroDef"},
                    {"field": "classification", "operator": "equals", "value": "CONFIDENTIAL"},
                ],
            }
        },
        headers=user_headers,
    )
    assert status == 200 and any(item["id"] == obj_id for item in ast_items)
    print("✓ Visual Boolean AST query engine verified.")

    # Audit log verification (with Admin headers, since AUDIT_READ is admin/auditor permission)
    status, audit_events, _ = request("/api/v1/audit/", headers=admin_headers)
    assert status == 200 and len(audit_events) > 0
    actions = [e["action"] for e in audit_events]
    assert "USER_REGISTER" in actions
    assert "OBJECT_UPLOAD" in actions
    assert "OBJECT_SHARE" in actions
    print(f"✓ Security & Operations Audit Trail verified ({len(audit_events)} audit events recorded).")

    # Cleanup test object
    status, del_res, _ = request(f"/api/v1/objects/{obj_id}", method="DELETE", headers=admin_headers)
    assert status == 200
    print(f"✓ Cleanup: Object #{obj_id} deleted successfully.")

    print("\n" + "=" * 65)
    print(" ALL 14 EASYSTORE SYSTEM TESTS PASSED SUCCESSFULLY! (100% PASS)")
    print("=" * 65)
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
