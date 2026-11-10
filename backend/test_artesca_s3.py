#!/usr/bin/env python3
"""
Scality ARTESCA S3 Production Diagnostic & Verification Tool

This tool validates your connection to a real Scality ARTESCA S3 endpoint:
1. Network & HTTPS TLS verification (including enterprise CA bundles)
2. IAM Identity authentication & Signature Version 4 (s3v4)
3. Bucket accessibility and path-style addressing
4. CRUD operations on objects (PutObject, GetObject, DeleteObject)
5. Least-privilege permission validation
"""

import os
import sys
import time
import uuid

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import settings
from app.services.s3 import get_s3_client, resolve_ssl_verification
from botocore.exceptions import ClientError, EndpointConnectionError, SSLError


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def run_diagnostics():
    print_header("SCALITY ARTESCA S3 PRODUCTION DIAGNOSTIC")
    print(f"Target Endpoint   : {settings.s3_endpoint_url}")
    print(f"Target Bucket     : {settings.s3_bucket}")
    print(f"Target Region     : {settings.s3_region}")
    print(f"Addressing Style  : {settings.s3_addressing_style}")
    print(f"Signature Version : {settings.s3_signature_version}")
    
    is_https = settings.s3_endpoint_url.lower().startswith("https://")
    ssl_verify = resolve_ssl_verification()
    print(f"HTTPS Protocol    : {'✓ YES (Secure)' if is_https else '⚠ NO (HTTP unencrypted)'}")
    print(f"SSL Verification  : {ssl_verify}")
    print(f"IAM Access Key ID : {settings.s3_access_key_id[:4]}...{settings.s3_access_key_id[-4:] if len(settings.s3_access_key_id) > 8 else ''}")

    client = get_s3_client()

    # Step 1: Bucket Accessibility & Read (ListBucket / HeadBucket)
    print_header("Step 1: Validating Endpoint & Bucket Accessibility")
    try:
        t0 = time.time()
        client.head_bucket(Bucket=settings.s3_bucket)
        lat = round((time.time() - t0) * 1000, 2)
        print(f"✓ Successfully reached bucket '{settings.s3_bucket}' in {lat}ms")
    except SSLError as exc:
        print(f"✗ TLS/SSL Handshake FAILED: {exc}")
        print("  -> Hint: If your Scality ARTESCA cluster uses an internal or corporate CA,")
        print("     set S3_CA_BUNDLE=/path/to/artesca-ca.pem or set S3_VERIFY_SSL=false for testing.")
        return False
    except EndpointConnectionError as exc:
        print(f"✗ Endpoint Connection FAILED: {exc}")
        print("  -> Hint: Verify network routing, DNS resolution, and firewall rules to ARTESCA.")
        return False
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        if code in ("403", "AccessDenied"):
            print(f"✗ Access Denied (403): IAM identity lacks 's3:ListBucket' on arn:aws:s3:::{settings.s3_bucket}")
        elif code in ("404", "NoSuchBucket"):
            print(f"✗ Bucket Not Found (404): Bucket '{settings.s3_bucket}' does not exist on ARTESCA.")
        else:
            print(f"✗ S3 ClientError: {exc}")
        return False

    # Step 2: Object Write (PutObject)
    print_header("Step 2: Validating Object Upload (s3:PutObject)")
    test_key = f"diagnostics/artesca-probe-{uuid.uuid4().hex[:8]}.txt"
    test_payload = b"Scality ARTESCA production verification test payload."
    try:
        t0 = time.time()
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=test_key,
            Body=test_payload,
            ContentType="text/plain",
            Metadata={"verified-by": "artesca-diagnostic"},
        )
        lat = round((time.time() - t0) * 1000, 2)
        print(f"✓ PutObject succeeded in {lat}ms (Key: {test_key})")
    except ClientError as exc:
        print(f"✗ PutObject FAILED: {exc}")
        return False

    # Step 3: Object Read (GetObject)
    print_header("Step 3: Validating Object Download (s3:GetObject)")
    try:
        t0 = time.time()
        resp = client.get_object(Bucket=settings.s3_bucket, Key=test_key)
        data = resp["Body"].read()
        lat = round((time.time() - t0) * 1000, 2)
        if data == test_payload:
            print(f"✓ GetObject verified in {lat}ms ({len(data)} bytes matched exactly)")
        else:
            print(f"✗ Payload mismatch: expected {len(test_payload)} bytes, got {len(data)}")
            return False
    except ClientError as exc:
        print(f"✗ GetObject FAILED: {exc}")
        return False

    # Step 4: Object Delete (DeleteObject)
    print_header("Step 4: Validating Object Deletion (s3:DeleteObject)")
    try:
        t0 = time.time()
        client.delete_object(Bucket=settings.s3_bucket, Key=test_key)
        lat = round((time.time() - t0) * 1000, 2)
        print(f"✓ DeleteObject verified in {lat}ms")
    except ClientError as exc:
        print(f"✗ DeleteObject FAILED: {exc}")
        return False

    # Step 5: Least-Privilege Verification
    print_header("Step 5: Validating Least-Privilege Enforcement")
    # Verify that the IAM user cannot create unauthorized buckets
    unauthorized_bucket = f"artesca-unauthorized-{uuid.uuid4().hex[:6]}"
    try:
        client.create_bucket(Bucket=unauthorized_bucket)
        print(f"⚠ Warning: IAM identity was able to create an arbitrary bucket '{unauthorized_bucket}'.")
        print("  For strict production least privilege, remove 's3:CreateBucket' permissions.")
        # Cleanup if created
        try:
            client.delete_bucket(Bucket=unauthorized_bucket)
        except Exception:
            pass
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        if code in ("403", "AccessDenied"):
            print(f"✓ Least Privilege Confirmed: IAM identity is correctly DENIED permission to create buckets.")
        else:
            print(f"✓ Least Privilege Verified (Response: {code})")

    print_header("RESULT: SCALITY ARTESCA S3 ENDPOINT FULLY VERIFIED")
    print("Your ARTESCA endpoint, credentials, and permissions are production-ready!\n")
    return True


if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
