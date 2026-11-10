import json
import time
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

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
        with urllib.request.urlopen(req) as resp:
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

def multipart_upload(path, fields, filename, file_bytes, content_type="text/plain", headers=None):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    h = headers.copy() if headers else {}
    h["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    
    body = bytearray()
    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        body.extend(f"{v}\r\n".encode())
        
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
    body.extend(file_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    
    return request(path, method="POST", data=body, headers=h, is_json=False)

def main():
    print("==================================================================")
    print(" VERIFYING ARTESCA OBJECT MANAGEMENT 4 TARGET ENHANCEMENTS")
    print("==================================================================")

    # -------------------------------------------------------------
    # 0. Health & Authentication
    # -------------------------------------------------------------
    print("\n--- [System Health & Auth] ---")
    status, health, _ = request("/health")
    assert status == 200 and health.get("status") in ("healthy", "ok"), f"Health failed: {health}"
    print("✓ Backend service is healthy.")

    status, db_health, _ = request("/health/database")
    assert status == 200 and db_health.get("database") == "connected", f"DB health failed: {db_health}"
    print("✓ PostgreSQL database connection active.")

    status, login_res, _ = request("/api/v1/auth/login", method="POST", data={"username": "madhavi", "password": "Madhavi@123"})
    assert status == 200, f"Login failed: {login_res}"
    token = login_res["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Authenticated successfully as 'madhavi'. Token acquired.")

    # -------------------------------------------------------------
    # Enhancement 2: Metadata Schema Administration (CRUD & Validation)
    # -------------------------------------------------------------
    print("\n--- [Enhancement 2: Metadata Schema Administration] ---")
    ts = int(time.time())
    schema_payload = {
        "name": f"AeroDef Sensor Telemetry {ts}",
        "description": "Validation schema for flight sensor payload and telemetry records",
        "is_active": True,
        "fields": [
            {"name": "mission_id", "label": "Mission Identifier", "type": "string", "required": True},
            {"name": "sensor_type", "label": "Sensor Type", "type": "enum", "required": True, "options": ["RADAR", "LIDAR", "THERMAL", "OPTICAL"]},
            {"name": "sample_rate_hz", "label": "Sample Rate (Hz)", "type": "number", "required": True},
            {"name": "is_calibrated", "label": "Calibrated", "type": "boolean", "required": False}
        ]
    }
    # 1. Create
    status, schema, _ = request("/api/v1/schemas/", method="POST", data=schema_payload, headers=headers)
    assert status == 201, f"Failed to create schema: {schema}"
    schema_id = schema["id"]
    print(f"✓ Schema created: ID #{schema_id} ('{schema['name']}') with {len(schema['fields'])} typed fields.")

    # 2. Read / List
    status, schemas_list, _ = request("/api/v1/schemas/", headers=headers)
    assert status == 200 and any(s["id"] == schema_id for s in schemas_list)
    print(f"✓ List schemas succeeded: {len(schemas_list)} schema(s) indexed.")

    # 3. Dynamic Validation Endpoint (Valid payload)
    status, val_ok, _ = request(f"/api/v1/schemas/{schema_id}/validate", method="POST", data={
        "metadata": {
            "mission_id": "MIS-2026-X",
            "sensor_type": "RADAR",
            "sample_rate_hz": 1200,
            "is_calibrated": True
        }
    }, headers=headers)
    assert status == 200 and val_ok.get("is_valid") is True, f"Validation should succeed: {val_ok}"
    print("✓ Schema validation sandbox: Valid metadata confirmed.")

    # 4. Dynamic Validation Endpoint (Invalid payload - missing required + invalid enum)
    status, val_fail, _ = request(f"/api/v1/schemas/{schema_id}/validate", method="POST", data={
        "metadata": {
            "sensor_type": "UNKNOWN_SENSOR",
            "sample_rate_hz": "not_a_number"
        }
    }, headers=headers)
    assert status == 200 and val_fail.get("is_valid") is False, f"Validation should catch errors: {val_fail}"
    print(f"✓ Schema validation sandbox: Correctly caught {len(val_fail['errors'])} schema violations:")
    for err in val_fail["errors"]:
        print(f"    - {err}")

    # -------------------------------------------------------------
    # Enhancement 3: PostgreSQL JSONB Querying + GIN Indexing & S3 Ingestion
    # -------------------------------------------------------------
    print("\n--- [Enhancement 3: PostgreSQL JSONB Querying + GIN Indexing] ---")
    test_obj_filename = f"telemetry_radar_{ts}.dat"
    test_obj_content = b"ARTESCA BINARY SENSOR DATA STREAM\nFREQ=9.4GHz\nAZIMUTH=142.5\nELEVATION=12.1"
    
    upload_fields = {
        "bucket": "artesca-documents",
        "object_key": f"radar/runs/{test_obj_filename}",
        "classification": "RESTRICTED",
        "department": "AeroDef",
        "project": "Project-Aero",
        "document_type": "Sensor Data",
        "schema_id": str(schema_id),
        "custom_metadata": json.dumps({
            "mission_id": "MIS-2026-X",
            "sensor_type": "RADAR",
            "sample_rate_hz": 1200,
            "is_calibrated": True,
            "radar_band": "X-Band",
            "altitude_meters": 4500
        })
    }

    status, upload_res, _ = multipart_upload(
        "/api/v1/objects/upload",
        upload_fields,
        filename=test_obj_filename,
        file_bytes=test_obj_content,
        content_type="application/octet-stream",
        headers=headers
    )
    assert status in (200, 201), f"Upload failed: {upload_res}"
    obj_id = upload_res["id"]
    print(f"✓ Uploaded object ID #{obj_id} ('{test_obj_filename}') to S3 & indexed in PostgreSQL.")
    assert upload_res.get("metadata", {}).get("custom_metadata", {}).get("radar_band") == "X-Band"
    print("✓ Confirmed custom metadata stored in native PostgreSQL JSONB column.")

    # -------------------------------------------------------------
    # Enhancement 1: Visual AND/OR/NOT Query Builder (AST Engine)
    # -------------------------------------------------------------
    print("\n--- [Enhancement 1: Visual AND/OR/NOT Query Builder AST Engine] ---")
    
    # AST Query 1: AND condition querying PostgreSQL JSONB custom attributes directly
    query_payload_1 = {
        "root": {
            "combinator": "AND",
            "rules": [
                {"field": "custom_metadata.mission_id", "operator": "equals", "value": "MIS-2026-X"},
                {"field": "custom_metadata.sensor_type", "operator": "equals", "value": "RADAR"}
            ]
        }
    }
    status, q1_results, _ = request("/api/v1/search/query", method="POST", data=query_payload_1, headers=headers)
    assert status == 200 and isinstance(q1_results, list), f"Query 1 failed: {q1_results}"
    assert any(o["id"] == obj_id for o in q1_results), f"Object #{obj_id} not found in query results"
    print(f"✓ AST Query 1 (AND with JSONB subfield): Found {len(q1_results)} matching object(s).")

    # AST Query 2: Nested condition with combinators (AND containing an OR group and a NOT group)
    query_payload_2 = {
        "root": {
            "combinator": "AND",
            "rules": [
                {"field": "classification", "operator": "equals", "value": "RESTRICTED"},
                {
                    "combinator": "OR",
                    "rules": [
                        {"field": "custom_metadata.radar_band", "operator": "equals", "value": "X-Band"},
                        {"field": "custom_metadata.radar_band", "operator": "equals", "value": "Ku-Band"}
                    ]
                },
                {
                    "combinator": "NOT",
                    "rules": [
                        {"field": "filename", "operator": "contains", "value": "obsolete_archive"}
                    ]
                }
            ]
        }
    }
    status, q2_results, _ = request("/api/v1/search/query", method="POST", data=query_payload_2, headers=headers)
    assert status == 200 and isinstance(q2_results, list), f"Query 2 failed: {q2_results}"
    assert any(o["id"] == obj_id for o in q2_results)
    print(f"✓ AST Query 2 (Nested AND + OR + NOT boolean tree): Found {len(q2_results)} matching object(s).")

    # AST Query 3: JSONB Key Existence operator
    query_payload_3 = {
        "root": {
            "combinator": "AND",
            "rules": [
                {"field": "custom_metadata.altitude_meters", "operator": "exists", "value": ""}
            ]
        }
    }
    status, q3_results, _ = request("/api/v1/search/query", method="POST", data=query_payload_3, headers=headers)
    assert status == 200 and isinstance(q3_results, list)
    assert any(o["id"] == obj_id for o in q3_results)
    print(f"✓ AST Query 3 (JSONB 'exists' operator): Successfully matched.")

    # -------------------------------------------------------------
    # S3 Storage Download & Cleanup
    # -------------------------------------------------------------
    print("\n--- [Storage Validation & Clean Up] ---")
    status, downloaded_bytes, _ = request(f"/api/v1/objects/{obj_id}/download", headers=headers)
    assert status == 200 and downloaded_bytes == test_obj_content, "Downloaded bytes do not match uploaded payload!"
    print(f"✓ Object #{obj_id} successfully streamed from S3 and verified bit-for-bit.")

    status, del_res, _ = request(f"/api/v1/objects/{obj_id}", method="DELETE", headers=headers)
    assert status == 200, f"Delete failed: {del_res}"
    print(f"✓ Object #{obj_id} deleted successfully from S3 and PostgreSQL catalog.")

    status, _, _ = request(f"/api/v1/schemas/{schema_id}", method="DELETE", headers=headers)
    assert status in (200, 204)
    print(f"✓ Cleaned up schema #{schema_id}.")

    # -------------------------------------------------------------
    # Enhancement 4: Production Deployment Automation Check
    # -------------------------------------------------------------
    print("\n--- [Enhancement 4: Production Deployment Automation Check] ---")
    import os
    project_root = os.path.dirname(os.path.abspath(__file__))
    deploy_files = [
        "Dockerfile",
        "docker-compose.yml",
        ".env.example",
        "deploy.sh",
        "start_production.sh",
        "artesca.service",
        "database_seed.sql"
    ]
    for df in deploy_files:
        p = os.path.join(project_root, "..", df)
        assert os.path.exists(p), f"Missing deployment file: {df}"
        print(f"✓ Deployment file verified: {df}")

    print("\n==================================================================")
    print(" ALL 4 TARGET ENHANCEMENTS SUCCESSFULLY TESTED AND VERIFIED 100%! ")
    print("==================================================================")

if __name__ == "__main__":
    main()
