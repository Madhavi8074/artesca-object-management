# EasyStore – A Web-Based Management Layer for S3-Compatible Object Storage

[![FastAPI](https://img.shields.io/badge/FastAPI-0.142-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Boto3](https://img.shields.io/badge/AWS%20S3-Boto3-FF9900?logo=amazons3&logoColor=white)](https://boto3.amazonaws.com)
[![MinIO](https://img.shields.io/badge/MinIO-Compatible-C72C48?logo=minio&logoColor=white)](https://min.io)
[![Scality ARTESCA](https://img.shields.io/badge/Scality-ARTESCA%20Ready-00A4E4)](https://www.scality.com/artesca)

---

## 1. Project Introduction

**EasyStore** is an enterprise-grade, web-based management and metadata indexing layer designed for S3-compatible object storage systems. Developed for research and internship demonstration at **DRDO-LRDE**, EasyStore addresses key limitations in native S3 storage by decoupling the **Data Storage Plane** (file payloads) from the **Metadata Control Plane** (searchable business metadata, hierarchical folders, schema enforcement, presigned share links, and audit compliance).

The system seamlessly targets **Scality ARTESCA** in production environments while using **MinIO** for local containerized development and offline demonstrations.

---

## 2. Project Objectives

1. **High-Performance Metadata Indexing**: Enable sub-millisecond multi-attribute queries and arbitrary JSON key-value filtering over S3 objects using PostgreSQL `JSONB` and GIN indexing, eliminating expensive linear `ListObjectsV2` bucket scans.
2. **Zero Credential Exposure**: Enforce strict security where browser clients never receive S3 access keys or secret credentials. All client file operations utilize time-limited cryptographic presigned URLs (HMAC-SHA256 / SigV4).
3. **Hierarchical Folder Management**: Provide pseudo-folder creation (`folder/` directory markers), prefix drill-down, and breadcrumb navigation over flat S3 namespaces.
4. **Dynamic Schema Administration**: Allow administrators to define, version, and enforce typed metadata schemas (string, number, boolean, date, enum) during file ingestion.
5. **Visual Query Engine**: Offer an intuitive visual Boolean AST (AND/OR/NOT) query builder alongside standard keyword filters.
6. **Regulatory Audit Trail**: Record an immutable, tamper-evident security audit log in PostgreSQL for all authentication events, uploads, downloads, share links, and deletions.
7. **Storage Flexibility**: Native compatibility with Scality ARTESCA and MinIO via standard `boto3` without vendor-specific proprietary lock-in.

---

## 3. Technologies Used

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite | Modern, zero-dependency responsive user interface |
| **Backend** | FastAPI, Python 3.12+, Uvicorn | High-throughput asynchronous REST API |
| **Database** | PostgreSQL 16 / SQLAlchemy 2.0 / Alembic | Relational metadata catalog, JSONB GIN indexing, RBAC, and audit logs |
| **Storage Driver** | Boto3, Botocore | Standard S3 API, SigV4 authentication, path-style addressing |
| **Dev Storage** | MinIO | Local S3-compatible development & containerized storage |
| **Prod Storage** | Scality ARTESCA | Target enterprise S3 object storage |
| **Security** | PyJWT, Pwdlib (Argon2id) | Cryptographic password hashing and JWT authentication |
| **Containerization** | Docker, Docker Compose | Multi-container automated orchestration |

---

## 4. System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION TIER (UI)                          │
│               React 19 • TypeScript • Vite • Vanilla CSS               │
│   • Dashboard & Storage Metrics        • Folder Navigation & Explorer │
│   • Multi-Attribute Catalog Search     • Drag & Drop File Upload      │
│   • Visual Boolean AST Query Builder   • Presigned Share Link Modal   │
│   • Metadata Schema Administration     • Immutable Audit Trail View   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS / REST (Bearer JWT Auth)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION TIER (API)                         │
│                    FastAPI (Python 3.12+) • Uvicorn                    │
│   • Auth & RBAC (/api/v1/auth)       • Object & Folder (/api/v1/objects)
│   • Search & Query (/api/v1/search)  • Metadata Schema (/api/v1/schemas)
│   • Audit Logging (/api/v1/audit)    • Health Probes (/health/*)       │
└───────────────────┬───────────────────────────────┬────────────────────┘
                    │                               │
       SQLAlchemy 2 │ Psycopg 3                     │ Boto3 S3 API (s3v4)
                    ▼                               ▼
┌───────────────────────────────┐   ┌────────────────────────────────────┐
│      METADATA CATALOG         │   │       OBJECT STORAGE TIER          │
│      PostgreSQL 16            │   │   MinIO (Dev) / Scality ARTESCA    │
│ • Object Properties & Schemas │   │ • Target Bucket: artesca-documents │
│ • JSONB GIN Indexes           │   │ • Binary File Payloads & Blobs     │
│ • Users, Roles & Permissions  │   │ • Path-Style Addressing & SigV4    │
│ • Immutable Audit Event Log   │   │ • Presigned URL Streaming          │
└───────────────────────────────┘   └────────────────────────────────────┘
```

---

## 5. Folder Structure

```text
easystore/
├── docker-compose.yml              # Multi-container orchestration (Postgres, MinIO, Backend, Frontend)
├── Dockerfile                      # Unified production container specification
├── .env.example                    # Environment variable configuration template
├── .gitignore                      # Git ignore rules for virtualenvs, logs, and artifacts
├── README.md                       # Comprehensive project documentation
├── PROJECT_DOCUMENTATION.md        # Technical architectural design document
├── run_backend.sh                  # Standalone backend launch script
├── run_frontend.sh                 # Standalone frontend launch script
├── start_all.sh                    # Dual-service local development runner
├── stop_all.sh                     # Service shutdown script
├── deploy.sh                       # Production deployment automation script
├── start_production.sh             # Production multi-worker runner
│
├── backend/                        # FastAPI Application
│   ├── Dockerfile                  # Dedicated backend Docker container
│   ├── requirements.txt            # Python dependencies (FastAPI, SQLAlchemy, Boto3, Argon2)
│   ├── alembic.ini                 # Database migration configuration
│   ├── init_db.py                  # Database bootstrapper & RBAC role/user seed script
│   ├── alembic/                    # Database version migrations
│   └── app/
│       ├── main.py                 # FastAPI application root & middleware setup
│       ├── api/                    # REST API route handlers
│       │   ├── auth.py             # User registration, login, and profile (/me)
│       │   ├── objects.py          # Buckets, folders, uploads, downloads, presigned shares
│       │   ├── search.py           # Multi-attribute search & visual AST query engine
│       │   ├── schemas.py          # Metadata schema definitions & validation
│       │   └── audit.py            # Immutable security audit logs
│       ├── models/                 # SQLAlchemy ORM database models
│       ├── schemas/                # Pydantic validation models
│       ├── services/               # Business logic & external drivers
│       │   ├── s3.py               # Enterprise S3 driver (Scality ARTESCA & MinIO)
│       │   ├── auth.py             # Password hashing, token creation & RBAC logic
│       │   ├── audit.py            # Security audit event logging
│       │   └── permissions.py      # RBAC permission decorator
│       └── db/
│           ├── database.py         # SQLAlchemy engine & session factory
│           └── session.py          # Environment settings configuration
│
├── frontend/                       # React 19 Frontend
│   ├── Dockerfile                  # Frontend multi-stage Nginx container
│   ├── nginx.conf                  # Nginx reverse proxy configuration for port 3000
│   ├── package.json                # Frontend package configuration (Vite, React 19, TS)
│   ├── vite.config.ts              # Vite server & proxy configuration (Port 3000)
│   ├── index.html                  # HTML entry point
│   └── src/
│       ├── App.tsx                 # Main application view coordinator
│       ├── main.tsx                # React DOM root entry
│       ├── components/             # Reusable UI views & modals
│       │   ├── LoginPage.tsx       # Sign In & Account Registration tabs
│       │   ├── Topbar.tsx          # Status indicator and user bar
│       │   ├── Sidebar.tsx         # Tab navigation & user badge
│       │   ├── DashboardView.tsx   # Platform overview & metrics
│       │   ├── SearchObjectsView.tsx # Folder explorer, search, and action toolbar
│       │   ├── UploadObjectView.tsx  # Drag-and-drop file upload with schema enforcement
│       │   ├── SchemaAdminView.tsx # Dynamic schema designer & validator
│       │   ├── AuditLogView.tsx    # Security & compliance audit ledger
│       │   ├── ShareModal.tsx      # Presigned link generation & copy modal
│       │   ├── NewFolderModal.tsx  # Virtual folder creation modal
│       │   ├── ObjectDetailModal.tsx # Full metadata inspection & editor modal
│       │   ├── DeleteConfirmModal.tsx # Safe deletion prompt
│       │   └── QueryBuilder.tsx    # Visual recursive AST Boolean query builder
│       ├── services/
│       │   └── api.ts              # Centralized typed HTTP API client
│       └── types/
│           └── index.ts            # TypeScript interfaces and data contracts
│
├── database/                       # Database Resources
│   └── database_seed.sql           # Pre-seeded database dump (schema, roles, users)
│
└── tests/                          # Automated Verification Test Suite
    ├── test_e2e.py                 # 14-scenario end-to-end integration tests
    └── run_all_tests.py            # Automated test runner with isolated test database
```

---

## 6. Prerequisites

- **Docker & Docker Compose**: Recommended for running the complete multi-service stack with a single command.
- **Node.js**: v20+ and npm (for standalone frontend development).
- **Python**: 3.10+ (for standalone backend development).
- **PostgreSQL**: 14+ with JSONB support (if running without Docker).

---

## 7. Quick Start with Docker Compose

The fastest way to start EasyStore with all containers (Postgres, MinIO, MinIO Provisioner, Backend, and Frontend) is:

```bash
# 1. Clone repository and navigate to directory
cd artesca-object-management

# 2. Configure environment (defaults work out-of-the-box for local MinIO)
cp .env.example .env

# 3. Build and launch all containers
docker compose up --build
```

### Containers Started:
1. `easystore-postgres`: PostgreSQL 16 on port `5432`.
2. `easystore-minio`: MinIO S3 API on port `9000`, Console on `9001`.
3. `easystore-minio-init`: Automates bucket creation (`artesca-documents`).
4. `easystore-backend`: FastAPI application on port `8000`.
5. `easystore-frontend`: React 19 app served via Nginx on port `3000`.

To stop the containers:
```bash
docker compose down
```

---

## 8. Local Standalone Setup (Without Docker)

### Step 1: Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database schema and seed default roles/users
python init_db.py

# Start FastAPI backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server on port 3000
npm run dev
```

### Step 3: Quick Start All Script
Alternatively, run the automated helper script:
```bash
./start_all.sh
```
To stop all services:
```bash
./stop_all.sh
```

---

## 9. Application URLs & Endpoints

| Service | URL | Description |
|---|---|---|
| **Frontend Web Application** | [http://localhost:3000](http://localhost:3000) | EasyStore Management Dashboard |
| **Backend API Root** | [http://localhost:8000](http://localhost:8000) | FastAPI Backend |
| **Interactive API Docs (Swagger UI)** | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI interactive documentation |
| **Alternative API Docs (ReDoc)** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Clean ReDoc API reference |
| **Backend Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Service operational status |
| **Database Health Check** | [http://localhost:8000/health/database](http://localhost:8000/health/database) | Active PostgreSQL probe |
| **Storage Health Check** | [http://localhost:8000/health/storage](http://localhost:8000/health/storage) | Active S3 bucket accessibility check |
| **MinIO Web Console** | [http://localhost:9001](http://localhost:9001) | MinIO administrative storage browser |

---

## 10. Default Seed Credentials

The database comes pre-configured with default credentials:

| Username | Password | Role | Description |
|---|---|---|---|
| `madhavi` | `Artesca123` | **ADMIN** | Full administrative rights (schema write, delete, user administration) |
| `editor` | `Artesca123` | **EDITOR** | Read/write rights (upload, read, update, download, folder creation) |

*You can also register a new account on the login page using the **Create Account** tab.*

---

## 11. Environment Variable Configuration

Create a `.env` file in the root directory (copied from `.env.example`):

```bash
# -------------------------------------------------------------
# Database Configuration
# -------------------------------------------------------------
POSTGRES_USER=madhavi
POSTGRES_PASSWORD=Madhavi123
POSTGRES_DB=artesca_metadata
DATABASE_URL=postgresql+psycopg://madhavi:Madhavi123@127.0.0.1:5432/artesca_metadata

# -------------------------------------------------------------
# Security & JWT
# -------------------------------------------------------------
SECRET_KEY=artesca-production-secret-replace-with-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=120

# -------------------------------------------------------------
# Storage Option A: MinIO (Default Local Development)
# -------------------------------------------------------------
S3_ENDPOINT_URL=http://127.0.0.1:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET=artesca-documents
S3_REGION=us-east-1
S3_VERIFY_SSL=false
S3_ADDRESSING_STYLE=path
S3_SIGNATURE_VERSION=s3v4

# -------------------------------------------------------------
# Storage Option B: Scality ARTESCA (Production Deployment)
# Uncomment the following when targeting real Scality ARTESCA:
# -------------------------------------------------------------
# S3_ENDPOINT_URL=https://s3.artesca.yourorganization.internal
# S3_ACCESS_KEY_ID=YOUR_ARTESCA_IAM_KEY
# S3_SECRET_ACCESS_KEY=YOUR_ARTESCA_IAM_SECRET
# S3_BUCKET=artesca-documents
# S3_REGION=us-east-1
# S3_VERIFY_SSL=true
# S3_CA_BUNDLE=/path/to/corporate-ca-bundle.pem
# S3_ADDRESSING_STYLE=path
# S3_SIGNATURE_VERSION=s3v4
```

---

## 12. Scality ARTESCA Compatibility & Switching

EasyStore was engineered with Scality ARTESCA enterprise object storage as its primary target:

1. **Path-Style Addressing**: Configured via Botocore `s3={"addressing_style": "path"}` to match Scality ARTESCA enterprise DNS requirements.
2. **Signature Version 4 (s3v4)**: Enforces AWS Signature Version 4 HMAC-SHA256 on all API requests.
3. **Enterprise TLS Verification**: Supports custom corporate CA bundles via `S3_CA_BUNDLE` or standard verification.
4. **Least-Privilege IAM**: Works under non-root IAM credentials requiring only `s3:ListBucket`, `s3:GetBucketLocation`, `s3:GetObject`, `s3:PutObject`, and `s3:DeleteObject`.
5. **Zero-Configuration Switch**: To switch from local MinIO to Scality ARTESCA, simply update `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, and `S3_SECRET_ACCESS_KEY` in `.env`. No code changes are needed!

---

## 13. Running Automated Tests

EasyStore includes a comprehensive 14-scenario integration test suite verifying health, registration, login, RBAC permission enforcement, metadata schemas, virtual folders, file ingestion, presigned share links, direct download streaming, JSONB search, visual AST queries, and audit logs:

```bash
# Run the test suite
python tests/run_all_tests.py
```

Expected output:
```text
=================================================================
 ALL 14 EASYSTORE SYSTEM TESTS PASSED SUCCESSFULLY! (100% PASS)
=================================================================
```

---

## 14. Main Features Walkthrough

### 1. User Registration & Role-Based Access Control (RBAC)
- Clean toggle between **Sign In** and **Create Account** on the login page.
- Password hashing with Argon2id and stateless JWT token authentication.
- Strict authorization enforcing permission checks on schema modifications and file operations.

### 2. Folder Navigation & Management
- Hierarchical pseudo-directory support (`folder/` S3 directory markers).
- Clickable breadcrumbs (`Location: Root / folder / subfolder`).
- One-click **+ New Folder** modal.

### 3. Presigned Share Links
- Generate time-limited download links (15 min, 1 hr, 24 hr, 7 days).
- Cryptographically signed using AWS SigV4.
- Safe client sharing with zero risk of storage credential leakage.

### 4. Dynamic Metadata Schemas
- Define custom typed schemas (strings, numbers, booleans, dates, enums).
- Real-time schema validation sandbox before file upload.
- Stored and indexed in PostgreSQL JSONB with sub-millisecond query performance.

### 5. Advanced Search & Visual Boolean AST Queries
- Search by filename, regex key pattern, size range, department, project, and custom JSON attributes.
- Visual Query Builder mode supporting nested AND/OR/NOT condition groups.

### 6. Compliance Audit Ledger
- Immutable logging of all user activities (`USER_LOGIN`, `USER_REGISTER`, `OBJECT_UPLOAD`, `OBJECT_DOWNLOAD`, `OBJECT_SHARE`, `OBJECT_DELETE`).
- Queryable and inspectable through the dedicated Audit Trail view.

---

## 15. License

Developed for DRDO-LRDE internship research and demonstration purposes. All rights reserved.
