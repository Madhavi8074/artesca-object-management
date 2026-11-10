import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.audit import router as audit_router
from app.api.objects import router as objects_router
from app.api.schemas import router as schemas_router
from app.api.search import router as search_router
from app.db.database import engine

app = FastAPI(
    title="EasyStore – S3-Compatible Object Management API",
    description="Web-based management layer for S3-compatible object storage (Scality ARTESCA & MinIO)",
    version="1.0.0",
)

# Robust CORS configuration supporting both Docker and local dev ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(objects_router)
app.include_router(search_router)
app.include_router(audit_router)
app.include_router(schemas_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "easystore-object-management",
        "version": "1.0.0",
    }


@app.get("/health/database")
def database_health():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "test": value,
    }


@app.get("/health/storage")
def storage_health():
    from app.services.s3 import check_s3_connection
    return check_s3_connection()


# Mount compiled frontend dist if available (for unified single-container execution)
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
