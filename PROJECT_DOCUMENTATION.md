# ARTESCA Object Management System
## Detailed Project Documentation & Technical Report

**Project Title:** Scality ARTESCA S3 Object Storage Management & Searchable Metadata Catalog  
**Author / Developer:** Madhavi  
**Architecture Domain:** Cloud Object Storage, Asynchronous Microservices, Enterprise Metadata Cataloging  
**Version:** 1.0.0 (Production & Offline Ready)  

---

## 1. Executive Summary & Abstract

Modern enterprise architectures increasingly rely on S3-compatible object storage to manage massive volumes of unstructured data (PDFs, disk images, CAD models, sensor outputs, medical scans). While S3 provides near-infinite horizontal scalability and high durability, native S3 APIs present significant limitations for enterprise search:
1. **Limited Metadata Searchability:** S3 object user-defined metadata cannot be searched across an entire bucket without performing expensive, linear bucket scans (`ListObjectsV2`).
2. **Lack of Granular Business Indexing:** Enterprises require multi-attribute indexing (e.g., department, confidentiality classification, project tags, custom JSON attributes) that cannot be queried with sub-millisecond latency using storage-layer primitives alone.
3. **Audit & Compliance Deficits:** Regulatory standards (SOC2, HIPAA, GDPR) demand immutable, queryable audit trails recording who uploaded, read, modified, or deleted each object.

**The Solution:**  
The **ARTESCA Object Management System** bridges this gap by decoupling the **Data Plane** (the raw blob payload) from the **Metadata Control Plane** (relational business metadata, custom JSON schemas, RBAC, and audit logs):
- **Object Storage Plane:** Scality ARTESCA enterprise S3-compatible storage (or local SeaweedFS S3) provides durable, streaming blob persistence.
- **Metadata Catalog Plane:** PostgreSQL with advanced `JSONB` indexing provides ACID transactions, relational integrity, and arbitrary key-value attribute searches with sub-millisecond query performance.
- **Application Tier:** An asynchronous **FastAPI** backend enforces enterprise Role-Based Access Control (RBAC), streams binary payloads directly to S3 with zero server disk buffering, and logs tamper-evident audit events.
- **Presentation Tier:** A responsive **React 19 + TypeScript** dashboard delivers an intuitive interface for multi-parameter searches, drag-and-drop uploads, real-time metadata schema validation, and audit inspection.

---

## 2. System Architecture & Component Interaction

The system follows a 4-tier modular enterprise architecture:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION TIER (UI)                          │
│               React 19 • TypeScript • Vite • Vanilla CSS               │
│   • Dashboard Overview                 • Drag & Drop Streaming Upload │
│   • Multi-Parameter Object Explorer    • Audit Ledger Inspector       │
│   • Object Detail & JSON Editor        • Role-Based Access Views       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS / RESTful API (Bearer JWT)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION TIER (API)                          │
│                   FastAPI (Python 3.10+) • Uvicorn                     │
│   • Authentication & RBAC Engine (/api/v1/auth)                        │
│   • Object Streaming & Lifecycle (/api/v1/objects)                     │
│   • Multi-Criteria & JSONB Search Service (/api/v1/search)             │
│   • Immutable Compliance Audit Logger (/api/v1/audit)                  │
│   • Storage & Database Health Probes (/health/*)                       │
└───────────────────┬───────────────────────────────┬────────────────────┘
                    │                               │
       SQLAlchemy 2 │ Psycopg 3                     │ Boto3 S3 API (s3v4)
                    ▼                               ▼
┌───────────────────────────────┐   ┌────────────────────────────────────┐
│      METADATA CATALOG         │   │       OBJECT STORAGE TIER          │
│      PostgreSQL 14+           │   │      Scality ARTESCA S3            │
│ • Catalog & Schema Registry   │   │ • Bucket: artesca-documents        │
│ • JSONB GIN Indexes           │   │ • Binary Payloads & File Blobs     │
│ • Users, Roles, Permissions   │   │ • Least-Privilege IAM Access       │
│ • Immutable Audit Event Log   │   │ • TLS / HTTPS Strict Encryption    │
└───────────────────────────────┘   └────────────────────────────────────┘
```

### Data Flow Lifecycles

#### A. File Upload & Metadata Ingestion Flow
1. User authenticates via `/api/v1/auth/login` and receives a signed JWT token.
2. User submits a file with business classification, department, and custom JSON attributes through the Upload UI.
3. The FastAPI handler validates the user's `OBJECT_UPLOAD` permission via the `@require_permission` decorator.
4. The file payload is streamed directly to Scality ARTESCA S3 using `s3_client.put_object(...)`.
5. Upon successful S3 persistence, a transactional record is written to PostgreSQL:
   - Primary object record in `objects` table (bucket, key, filename, size, MIME type, owner ID).
   - Detailed metadata record in `object_metadata` table (classification, department, project, and `custom_metadata` JSONB).
6. An immutable audit record is committed to `audit_events` with the action `UPLOAD`, actor ID, timestamp, and client IP.
7. If the database transaction fails, an automated compensation routine rolls back and cleans up the orphan object from S3.

#### B. Multi-Criteria Catalog Search Flow
1. User filters objects by combining standard parameters (filename substring, key pattern, byte size bounds, classification) and arbitrary key-value pairs (e.g. `tier="archive"`).
2. The search service constructs an optimized SQL query using SQLAlchemy 2.0.
3. Custom JSON attributes are queried using PostgreSQL's native `JSONB` containment operators (`@>`), bypassing full table scans.
4. Matching catalog entries are returned with pagination and full metadata in under 15ms.

---

## 3. Technology Stack & Design Decisions

| Tier | Technology | Version | Rationale & Enterprise Benefits |
| :--- | :--- | :--- | :--- |
| **Object Storage** | **Scality ARTESCA S3** (or SeaweedFS S3) | S3v4 | Enterprise-grade S3 compatibility, high throughput, HTTPS encryption, IAM least-privilege policies. |
| **Relational Database** | **PostgreSQL** | 14+ | ACID compliance for mission-critical metadata, native `JSONB` indexing, foreign key constraints, robust audit ledger. |
| **Backend Framework** | **FastAPI (Python)** | 0.142+ | Asynchronous event loop (ASGI), automatic OpenAPI/Swagger documentation, strict Pydantic v2 data validation. |
| **ORM & Database Driver** | **SQLAlchemy + Psycopg 3** | 2.1+ / 3.3+ | Modern 2.0-style queries, thread-safe connection pooling, native PostgreSQL binary protocol support. |
| **Security & Auth** | **Argon2id + PyJWT** | — | Memory-hard password hashing (resistant to GPU cracking); stateless cryptographically signed JWT bearer tokens. |
| **Frontend Framework** | **React + TypeScript** | 19.0+ | Type-safe declarative UI components, instant state reactivity, predictable data modeling. |
| **Build Tool & Bundler** | **Vite** | 8.3+ | Lightning-fast HMR during development; optimized zero-external-dependency production build for 100% offline serving. |
| **Styling** | **Custom Design System (Vanilla CSS)** | — | Dark-mode enterprise palette, glassmorphism, micro-animations, zero heavy framework bloat. |

---

## 4. Database Schema & Data Modeling

The relational schema is normalized into 7 tables with strict foreign key constraints and cascade rules:

```text
 ┌──────────────────────┐         ┌──────────────────────┐
 │        users         │         │        roles         │
 ├──────────────────────┤         ├──────────────────────┤
 │ id (PK)              │◄───┐ ┌─►│ id (PK)              │
 │ username (UNIQUE)    │    │ │  │ name (ADMIN, EDITOR) │
 │ email                │    │ │  │ description          │
 │ password_hash        │    │ │  └──────────┬───────────┘
 │ is_active            │    │ │             │ 1
 └──────────┬───────────┘    │ │             │
            │ 1              │ │             │ N
            │          ┌─────┴─┴──────┐┌─────▼───────────────┐
            │          │  user_roles  ││  role_permissions   │
            │          ├──────────────┤├─────────────────────┤
            │          │ user_id (FK) ││ role_id (FK)        │
            │          │ role_id (FK) ││ permission_id (FK)  │
            │          └──────────────┘└─────┬───────────────┘
            │                                │ N
            │                                │ 1
            │ 1                              ▼
            │                         ┌──────────────────────┐
            │                         │     permissions      │
            │                         ├──────────────────────┤
            │                         │ id (PK)              │
            │                         │ code (e.g. UPLOAD)   │
            │                         │ description          │
            │                         └──────────────────────┘
            │
            │ N
            ▼
 ┌──────────────────────┐         ┌──────────────────────┐
 │       objects        │ 1     1 │   object_metadata    │
 ├──────────────────────┼────────►├──────────────────────┤
 │ id (PK)              │         │ id (PK)              │
 │ bucket               │         │ object_id (FK, UQ)   │
 │ object_key (UNIQUE)  │         │ title                │
 │ filename             │         │ description          │
 │ content_type         │         │ classification       │
 │ size_bytes           │         │ department           │
 │ owner_id (FK->users) │         │ project              │
 │ status (ACTIVE)      │         │ custom_metadata(JSONB│
 └──────────┬───────────┘         └──────────────────────┘
            │ 1
            │
            │ N
            ▼
 ┌──────────────────────┐
 │     audit_events     │
 ├──────────────────────┤
 │ id (PK)              │
 │ action (UPLOAD, etc) │
 │ user_id (FK->users)  │
 │ object_id (FK->objs) │
 │ details (JSONB)      │
 │ ip_address           │
 │ timestamp            │
 └──────────────────────┘
```

### Table Definitions

1. **`users`**:
   - `id` (Serial, Primary Key)
   - `username` (VARCHAR 64, Unique, Indexed)
   - `email` (VARCHAR 128, Unique)
   - `password_hash` (VARCHAR 255, Argon2id hash)
   - `display_name` (VARCHAR 128)
   - `department` (VARCHAR 64)
   - `is_active` (BOOLEAN, default True)
   - `created_at` / `updated_at` (TIMESTAMP WITH TIME ZONE)

2. **`roles` & `permissions` (RBAC)**:
   - `roles`: Pre-populated with `ADMIN`, `EDITOR`, and `VIEWER`.
   - `permissions`: Fine-grained privileges:
     - `OBJECT_UPLOAD`: Stream new files and register metadata.
     - `OBJECT_READ`: Browse catalog, view details, search metadata.
     - `OBJECT_UPDATE`: Modify business metadata and custom tags.
     - `OBJECT_DOWNLOAD`: Stream files from S3 to client.
     - `OBJECT_DELETE`: Permanently remove files from S3 and catalog.
     - `AUDIT_READ`: Inspect system-wide security audit trails.

3. **`objects`**:
   - `id` (Serial, Primary Key)
   - `bucket` (VARCHAR 63, Target S3 bucket)
   - `object_key` (VARCHAR 1024, Unique S3 object key)
   - `filename` (VARCHAR 255, Original user file name)
   - `content_type` (VARCHAR 128, MIME type)
   - `size_bytes` (BIGINT, Exact byte size)
   - `owner_id` (INTEGER, Foreign Key referencing `users.id`)
   - `status` (VARCHAR 32, e.g., `ACTIVE`, `DELETED`)
   - `created_at` / `updated_at` (TIMESTAMP WITH TIME ZONE)

4. **`object_metadata`**:
   - `id` (Serial, Primary Key)
   - `object_id` (INTEGER, Unique, Foreign Key referencing `objects.id` on delete CASCADE)
   - `title`, `description`, `author`, `department`, `project`, `document_type` (Indexed VARCHARs)
   - `classification` (VARCHAR 32: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`)
   - `custom_metadata` (**JSONB**): Flexible, schema-free JSON document allowing arbitrary enterprise attributes (e.g. `{"retention_years": 7, "regulatory_compliance": ["HIPAA", "PCI"]}`).

5. **`audit_events`**:
   - `id` (Serial, Primary Key)
   - `action` (VARCHAR 32: `LOGIN`, `UPLOAD`, `DOWNLOAD`, `UPDATE_METADATA`, `DELETE`)
   - `user_id` (INTEGER, Foreign Key referencing `users.id`)
   - `object_id` (INTEGER, Nullable Foreign Key referencing `objects.id` on delete SET NULL)
   - `details` (**JSONB**): Detailed event payload (e.g. previous vs updated metadata diffs, client user-agent).
   - `ip_address` (VARCHAR 45, Client IPv4/IPv6 address)
   - `timestamp` (TIMESTAMP WITH TIME ZONE, default UTC NOW)

---

## 5. Security & Least-Privilege IAM Integration

### A. Authentication & Password Security
- Passwords are encrypted using **Argon2id** (`m=65536, t=3, p=4`), the winner of the Password Hashing Competition, offering superior protection against side-channel and GPU-based brute-force attacks.
- Access tokens are cryptographically signed using **JWT (JSON Web Tokens)** with HMAC-SHA256 (`HS256`), containing user ID, role claims, and strict expiration timestamps.

### B. Scality ARTESCA S3 Least-Privilege IAM Policy
In a production deployment, the application connects to Scality ARTESCA using a dedicated IAM Service Identity with strict least-privilege scoping ([artesca-iam-policy.json](file:///home/madhavi/projects/artesca-object-management/artesca-iam-policy.json)):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBucketOperations",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::artesca-documents"
    },
    {
      "Sid": "AllowObjectOperations",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:AbortMultipartUpload",
        "s3:ListMultipartUploadParts"
      ],
      "Resource": "arn:aws:s3:::artesca-documents/*"
    },
    {
      "Sid": "EnforceTLSRequestsOnly",
      "Effect": "Deny",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::artesca-documents",
        "arn:aws:s3:::artesca-documents/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

**Security Principles Enforced:**
1. **Zero Bucket Proliferation:** The identity is strictly barred from calling `s3:CreateBucket` or `s3:DeleteBucket`.
2. **Blast Radius Containment:** The IAM policy grants permissions *only* to `artesca-documents`. All other enterprise buckets on the ARTESCA cluster are inaccessible.
3. **Mandatory HTTPS:** Unencrypted HTTP traffic is explicitly denied at the storage layer via the `aws:SecureTransport` condition.

---

## 6. REST API Specification

### Authentication Endpoints (`/api/v1/auth`)
| Method | Endpoint | Description | Auth Required | Request Body / Parameters |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Exchange credentials for JWT bearer token | No | `{"username": "...", "password": "..."}` |
| `GET` | `/api/v1/auth/me` | Retrieve profile and granted permissions | Bearer JWT | None |

### Object Management Endpoints (`/api/v1/objects`)
| Method | Endpoint | Description | Required Permission | Input / Parameters |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/objects/upload` | Stream file to S3 and catalog metadata | `OBJECT_UPLOAD` | Multipart Form: `file`, `object_key`, metadata fields |
| `GET` | `/api/v1/objects/` | List all active objects | `OBJECT_READ` | None |
| `GET` | `/api/v1/objects/{id}` | Retrieve complete object details & metadata | `OBJECT_READ` | Object ID (path) |
| `GET` | `/api/v1/objects/{id}/download` | Stream binary file payload from S3 | `OBJECT_DOWNLOAD` | Object ID (path) |
| `PUT` | `/api/v1/objects/{id}/metadata` | Update business metadata & JSON attributes | `OBJECT_UPDATE` | JSON payload with updated metadata fields |
| `DELETE` | `/api/v1/objects/{id}` | Delete object from S3 & mark catalog record | `OBJECT_DELETE` | Object ID (path) |

### Search & Discovery Endpoints (`/api/v1/search`)
| Method | Endpoint | Description | Required Permission | Supported Filters |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/search/objects` | Multi-criteria catalog search | `OBJECT_READ` | `filename`, `object_key`, `object_key_regex`, `content_type`, `bucket`, `size_bytes`, `size_operator` (`gt`/`lt`/`eq`), `classification`, `department`, `project`, `author`, `custom_key`, `custom_value` |

### Audit & Security Endpoints (`/api/v1/audit`)
| Method | Endpoint | Description | Required Permission | Input / Parameters |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/audit/` | System-wide audit event ledger | `AUDIT_READ` | None (returns recent 100 audit events) |
| `GET` | `/api/v1/audit/object/{id}` | Per-object audit lifecycle history | `AUDIT_READ` | Object ID (path) |

### Health & Monitoring Endpoints (`/health`)
| Method | Endpoint | Description | Response Details |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Core microservice health check | Service status (`ok`) and version |
| `GET` | `/health/database` | PostgreSQL connection probe | Database connectivity state and probe query |
| `GET` | `/health/storage` | Scality ARTESCA S3 storage probe | Endpoint URL, bucket accessibility, latency in ms, TLS status |

---

## 7. Frontend Architecture & User Interface

The frontend is built using **React 19** with **TypeScript** and modular vanilla CSS:
- **`LoginPage.tsx`**: Clean, production-style login form with validation, error banners, and direct JWT token storage.
- **`Sidebar.tsx`**: Brand header, active role badge (e.g., `ADMIN`, `EDITOR`), navigational links with active states, and secure logout.
- **`Topbar.tsx`**: Page title context, live operational status badge (`Storage & DB Online`), and logged-in user identity avatar.
- **`DashboardView.tsx`**: Metrics dashboard showing total cataloged objects, storage capacity consumed, active buckets, and audit event counters.
- **`SearchObjectsView.tsx`**: Rich multi-parameter search bar with real-time filtering, byte-size comparator logic, metadata pill tags, and dynamic data table.
- **`UploadObjectView.tsx`**: Drag-and-drop file upload zone, automatic MIME detection, structured business attribute fields, and live JSON syntax validator.
- **`AuditLogView.tsx`**: Compliance audit ledger with timestamp formatting, actor tracking, and expandable JSON payload viewer.
- **`ObjectDetailModal.tsx` & `DeleteConfirmModal.tsx`**: Interactive modals for viewing S3 storage properties, editing custom metadata, and confirming destructive deletions.

---

## 8. Verification & Diagnostic Tooling

The project includes an automated diagnostic CLI script ([backend/test_artesca_s3.py](file:///home/madhavi/projects/artesca-object-management/backend/test_artesca_s3.py)) that validates production S3 connectivity across 5 verification steps:

```bash
backend/.venv/bin/python backend/test_artesca_s3.py
```

**Verification Results:**
1. **Endpoint Reachability:** Verifies DNS resolution and TCP handshake to target S3 storage.
2. **TLS / HTTPS Handshake:** Validates SSL certificate validity (supporting internal corporate CAs).
3. **IAM Authentication:** Validates Access Key ID and Secret Access Key using AWS Signature Version 4.
4. **CRUD Lifecycle:** Successfully tests `s3:PutObject`, `s3:GetObject`, and `s3:DeleteObject` probe cycles.
5. **Least-Privilege Enforcement:** Verifies that administrative operations (such as `s3:CreateBucket`) are properly denied by the IAM policy.

---

## 9. Offline Portability & Deployment Guide

The project is engineered to run seamlessly in **two deployment modes**:

### Mode A: 100% Offline Demonstration Mode (For Viva / Guide Review)
- Zero external internet access required.
- Pre-downloaded Python wheels in `backend/wheels/`.
- Pre-compiled production React build in `frontend/dist/` (served directly by FastAPI on port 8000; Node.js is not even needed on the demo machine).
- Standalone native S3 binary (`weed`) pre-bundled in the root folder (Docker is optional).
- Pre-configured database dump (`database_seed.sql`) with admin (`madhavi`) and editor (`editor`) accounts.

**Execution Commands:**
```bash
# 1. One-time automated setup:
./setup_offline.sh

# 2. Start all services:
./start_all.sh

# 3. Access in browser:
http://127.0.0.1:8000
```

### Mode B: Production Enterprise Scality ARTESCA Mode
To switch from local development to a live enterprise Scality ARTESCA cluster:
1. Update `backend/.env`:
   ```ini
   S3_ENDPOINT_URL=https://s3.artesca.yourcompany.com
   S3_ACCESS_KEY_ID=YOUR_ARTESCA_IAM_ACCESS_KEY
   S3_SECRET_ACCESS_KEY=YOUR_ARTESCA_IAM_SECRET_KEY
   S3_BUCKET=artesca-documents
   S3_REGION=us-east-1
   S3_VERIFY_SSL=true
   S3_ADDRESSING_STYLE=path
   S3_SIGNATURE_VERSION=s3v4
   ```
2. Verify connection:
   ```bash
   backend/.venv/bin/python backend/test_artesca_s3.py
   ```
3. Restart backend:
   ```bash
   ./run_backend.sh
   ```

---

## 10. Conclusion & Future Roadmap

The ARTESCA Object Management System demonstrates an enterprise-grade pattern for modern cloud object storage:
- High-performance blob storage without losing rich, fast, queryable metadata.
- Strict security with Argon2id, JWT, and S3 IAM least-privilege policies.
- Regulatory auditability with immutable event logs.
- Extreme portability with 100% offline self-contained execution.

### Future Roadmap
1. **Multipart Upload Resumption:** Chunked streaming for multi-gigabyte files.
2. **Object Versioning Support:** S3 version ID tracking with historical metadata rollback.
3. **Automated Lifecycle Policies:** Scheduled transition of objects to colder storage tiers based on JSONB metadata retention rules.
4. **Vector Search Integration:** Generating embeddings for cataloged documents for semantic similarity search.

---
*Documentation compiled and maintained by Madhavi &bull; ARTESCA Object Management Project*
