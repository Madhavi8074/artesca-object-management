import os
import time
from typing import Any, Dict, List, Optional, Union
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError, SSLError

from app.db.session import settings


def resolve_ssl_verification() -> Union[bool, str]:
    """
    Resolve the SSL verification parameter for boto3.
    Supports:
      - Custom CA bundle path via s3_ca_bundle or s3_verify_ssl (for internal ARTESCA certificates)
      - Boolean True / False for standard public CA or self-signed dev setups
    """
    if settings.s3_ca_bundle and os.path.isfile(settings.s3_ca_bundle):
        return settings.s3_ca_bundle

    if isinstance(settings.s3_verify_ssl, str):
        val = settings.s3_verify_ssl.strip()
        if os.path.isfile(val):
            return val
        if val.lower() in ("false", "0", "no", "off"):
            return False
        if val.lower() in ("true", "1", "yes", "on"):
            return True

    return bool(settings.s3_verify_ssl)


def create_s3_config() -> Config:
    """
    Build Botocore client configuration tailored for Scality ARTESCA enterprise S3 and MinIO.
    Enforces Signature Version 4 (s3v4), path-style addressing, and production connection pools.
    """
    return Config(
        signature_version=settings.s3_signature_version or "s3v4",
        s3={
            "addressing_style": settings.s3_addressing_style or "path",
        },
        retries={
            "max_attempts": 3,
            "mode": "standard",
        },
        max_pool_connections=50,
        connect_timeout=10,
        read_timeout=30,
    )


def get_s3_client():
    """
    Factory to construct a Boto3 S3 client configured for Scality ARTESCA or MinIO.
    """
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
        verify=resolve_ssl_verification(),
        config=create_s3_config(),
    )


# Shared global S3 client
s3_client = get_s3_client()


def list_buckets() -> List[Dict[str, Any]]:
    """List accessible S3 buckets."""
    response = s3_client.list_buckets()
    return [
        {
            "name": bucket["Name"],
            "created_at": bucket.get("CreationDate"),
        }
        for bucket in response.get("Buckets", [])
    ]


def head_object(bucket: str, key: str) -> Dict[str, Any]:
    """Retrieve metadata for a specific S3 object without fetching payload."""
    return s3_client.head_object(Bucket=bucket, Key=key)


def create_folder(bucket: str, folder_key: str) -> Dict[str, Any]:
    """
    Create a pseudo-folder in S3-compatible storage by writing a 0-byte object with trailing slash.
    """
    clean_folder = folder_key.strip().rstrip("/") + "/"
    s3_client.put_object(
        Bucket=bucket,
        Key=clean_folder,
        Body=b"",
        ContentType="application/x-directory",
    )
    return {"bucket": bucket, "folder_key": clean_folder}


def generate_presigned_download_url(
    bucket: str,
    key: str,
    filename: Optional[str] = None,
    expires_in: int = 3600,
) -> str:
    """
    Generate a presigned GET URL for secure, time-limited direct download.
    Never exposes credentials to browser or client.
    """
    params = {
        "Bucket": bucket,
        "Key": key,
    }
    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params=params,
        ExpiresIn=expires_in,
    )


def generate_presigned_upload_url(
    bucket: str,
    key: str,
    content_type: str = "application/octet-stream",
    expires_in: int = 3600,
) -> Dict[str, Any]:
    """
    Generate a presigned PUT URL for direct-to-S3 client uploads.
    """
    url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )
    return {
        "upload_url": url,
        "method": "PUT",
        "bucket": bucket,
        "key": key,
        "expires_in": expires_in,
    }


def ensure_bucket_exists(bucket: str) -> bool:
    """Ensure that the target bucket exists, creating it if necessary."""
    try:
        s3_client.head_bucket(Bucket=bucket)
        return True
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in ("404", "NoSuchBucket"):
            try:
                s3_client.create_bucket(Bucket=bucket)
                return True
            except Exception:
                return False
        return False
    except Exception:
        return False


def check_s3_connection() -> Dict[str, Any]:
    """
    Performs an active health and connectivity check against the S3 endpoint.
    Verifies endpoint availability, TLS negotiation, and least-privilege bucket access.
    """
    start_time = time.time()
    ssl_verify = resolve_ssl_verification()
    is_https = settings.s3_endpoint_url.lower().startswith("https://")

    info: Dict[str, Any] = {
        "status": "connected",
        "endpoint_url": settings.s3_endpoint_url,
        "bucket": settings.s3_bucket,
        "region": settings.s3_region,
        "protocol": "HTTPS" if is_https else "HTTP",
        "is_https": is_https,
        "addressing_style": settings.s3_addressing_style,
        "ssl_verification": str(ssl_verify) if isinstance(ssl_verify, str) else bool(ssl_verify),
    }

    try:
        s3_client.head_bucket(Bucket=settings.s3_bucket)
        info["latency_ms"] = round((time.time() - start_time) * 1000, 2)
        info["bucket_accessible"] = True
        return info

    except SSLError as exc:
        info["status"] = "error"
        info["error_type"] = "SSLError"
        info["message"] = (
            f"TLS/SSL certificate verification failed when connecting to {settings.s3_endpoint_url}. "
            f"If ARTESCA uses a private or corporate CA certificate, provide the CA bundle path in S3_CA_BUNDLE "
            f"or set S3_VERIFY_SSL=false for testing. Details: {str(exc)}"
        )
        return info

    except EndpointConnectionError as exc:
        info["status"] = "error"
        info["error_type"] = "EndpointConnectionError"
        info["message"] = (
            f"Cannot connect to S3 endpoint at {settings.s3_endpoint_url}. "
            f"Check hostname, IP address, network routes, and port numbers. Details: {str(exc)}"
        )
        return info

    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        info["latency_ms"] = round((time.time() - start_time) * 1000, 2)

        if error_code in ("403", "AccessDenied"):
            info["status"] = "error"
            info["error_type"] = "AccessDenied"
            info["message"] = (
                f"Access denied to bucket '{settings.s3_bucket}'. "
                f"Verify that your S3 IAM policy grants 's3:ListBucket' and 's3:GetBucketLocation' "
                f"on arn:aws:s3:::{settings.s3_bucket} to IAM user '{settings.s3_access_key_id}'."
            )
            return info
        elif error_code in ("404", "NoSuchBucket"):
            info["status"] = "error"
            info["error_type"] = "NoSuchBucket"
            info["message"] = (
                f"Target bucket '{settings.s3_bucket}' was not found. "
                f"Create the bucket in storage management console or check bucket name."
            )
            return info
        else:
            info["status"] = "error"
            info["error_type"] = error_code
            info["message"] = str(exc)
            return info

    except Exception as exc:
        info["status"] = "error"
        info["error_type"] = type(exc).__name__
        info["message"] = str(exc)
        return info
