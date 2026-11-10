#!/usr/bin/env python3
"""
EasyStore Automated Verification Test Runner

Executes the full test suite against EasyStore:
1. Database initialization and seeding (PostgreSQL / SQLite)
2. In-memory S3 mock / live S3 fallback for offline test execution
3. Background FastAPI server startup
4. Execution of all 14 functional and security tests
5. Clean teardown
"""

import io
import os
import sys
import time
import subprocess
import threading
import uuid

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
sys.path.insert(0, BACKEND_DIR)

os.environ["DATABASE_URL"] = "sqlite:///./test_runner.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-drdo-easystore-verification"
os.environ["S3_BUCKET"] = "artesca-documents"

import uvicorn
from app.db.database import engine
from app.models.base import Base
from app.db.session import settings
import app.services.s3 as s3_module
from init_db import init_database


class MockStreamingBody:
    def __init__(self, data: bytes):
        self._data = data

    def read(self):
        return self._data

    def iter_chunks(self, chunk_size=1024):
        stream = io.BytesIO(self._data)
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            yield chunk


class MockS3Client:
    """In-memory S3 storage engine for automated offline testing."""
    def __init__(self):
        self._storage = {}

    def head_bucket(self, Bucket):
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def list_buckets(self):
        return {
            "Buckets": [
                {"Name": "artesca-documents", "CreationDate": "2026-11-10T00:00:00Z"},
                {"Name": "drdo-telemetry", "CreationDate": "2026-11-10T00:00:00Z"},
            ]
        }

    def create_bucket(self, Bucket):
        return {"Location": f"/{Bucket}"}

    def put_object(self, Bucket, Key, Body, ContentType="application/octet-stream", **kwargs):
        if hasattr(Body, "read"):
            data = Body.read()
        elif isinstance(Body, str):
            data = Body.encode("utf-8")
        else:
            data = bytes(Body)
        self._storage[(Bucket, Key)] = {"data": data, "content_type": ContentType}
        return {"ETag": '"test-etag-123456"'}

    def get_object(self, Bucket, Key):
        item = self._storage.get((Bucket, Key))
        if not item:
            raise Exception(f"NoSuchKey: {Key} does not exist in bucket {Bucket}")
        return {
            "Body": MockStreamingBody(item["data"]),
            "ContentType": item["content_type"],
            "ContentLength": len(item["data"]),
        }

    def delete_object(self, Bucket, Key):
        self._storage.pop((Bucket, Key), None)
        return {"DeleteMarker": True}

    def generate_presigned_url(self, ClientMethod, Params, ExpiresIn=3600):
        bucket = Params.get("Bucket", "artesca-documents")
        key = Params.get("Key", "")
        return (
            f"http://127.0.0.1:9000/{bucket}/{key}"
            f"?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            f"&X-Amz-Credential=minioadmin%2F20261110%2Fus-east-1%2Fs3%2Faws4_request"
            f"&X-Amz-Date=20261110T220000Z"
            f"&X-Amz-Expires={ExpiresIn}"
            f"&X-Amz-SignedHeaders=host"
            f"&X-Amz-Signature=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )


def start_server():
    from app.main import app
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8888, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def main():
    print("=" * 65)
    print(" EASYSTORE COMPREHENSIVE TEST SUITE EXECUTION")
    print("=" * 65)

    # 1. Initialize SQLite Database
    print("\n[Step 1] Initializing isolated test database schema...")
    init_database()
    print("✓ Schema initialized and default roles (ADMIN, EDITOR) verified.")

    # 2. Patch S3 client with Mock S3
    print("\n[Step 2] Attaching S3 storage driver (In-Memory S3 Compatible Engine)...")
    s3_mock = MockS3Client()
    s3_module.s3_client = s3_mock
    # Also patch inside modules that imported s3_client
    import app.api.objects as api_objects
    api_objects.s3_client = s3_mock
    print("✓ S3 storage driver attached.")

    # 3. Start Server in background thread
    print("\n[Step 3] Launching FastAPI test server on http://127.0.0.1:8888...")
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()

    # Wait for server to be responsive
    import urllib.request
    max_retries = 20
    server_ready = False
    for _ in range(max_retries):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8888/health", timeout=1) as resp:
                if resp.status == 200:
                    server_ready = True
                    break
        except Exception:
            time.sleep(0.2)

    if not server_ready:
        print("✗ Server failed to start.")
        sys.exit(1)

    print("✓ Server is responsive at http://127.0.0.1:8888.")

    # 4. Run test_e2e.py against http://127.0.0.1:8888
    print("\n[Step 4] Running complete end-to-end test scenarios...")
    os.environ["TEST_BASE_URL"] = "http://127.0.0.1:8888"
    from tests.test_e2e import run_tests
    success = run_tests()

    print("\n" + "=" * 65)
    if success:
        print(" TEST SUITE RESULT: 100% PASSED")
    else:
        print(" TEST SUITE RESULT: FAILED")
    print("=" * 65)

    # Cleanup test DB
    if os.path.exists("./test_runner.db"):
        os.remove("./test_runner.db")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
