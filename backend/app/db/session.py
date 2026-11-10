import os
from typing import Union
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_ENV_PATH = os.path.join(_BACKEND_DIR, ".env")
_ROOT_ENV_PATH = os.path.join(os.path.dirname(_BACKEND_DIR), ".env")


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://madhavi:Madhavi123@127.0.0.1:5432/artesca_metadata"
    secret_key: str = "artesca-production-secret-replace-with-openssl-rand-hex-32"
    access_token_expire_minutes: int = 120

    s3_endpoint_url: str = "http://127.0.0.1:9000"
    s3_access_key_id: str = "minioadmin"
    s3_secret_access_key: str = "minioadmin"
    s3_region: str = "us-east-1"
    s3_bucket: str = "artesca-documents"
    s3_verify_ssl: Union[bool, str] = False
    s3_addressing_style: str = "path"  # 'path' (standard for Scality ARTESCA and MinIO), 'virtual', or 'auto'
    s3_ca_bundle: str = ""  # Optional path to custom CA certificate for enterprise HTTPS
    s3_signature_version: str = "s3v4"

    @property
    def s3_access_key(self) -> str:
        return self.s3_access_key_id

    @property
    def s3_secret_key(self) -> str:
        return self.s3_secret_access_key

    model_config = SettingsConfigDict(
        env_file=(_ENV_PATH, _ROOT_ENV_PATH, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
