import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Skip cover page

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Header
        self.drawString(54, 11 * inch - 36, "Scality ARTESCA Object Management — Technical Project Documentation")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Running Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 36, page_str)
        self.drawString(54, 36, "CONFIDENTIAL & PROPRIETARY — DEFENSE RESEARCH & DEVELOPMENT (DRDO)")
        self.line(54, 46, 8.5 * inch - 54, 46)
        self.restoreState()

def create_pdf(filename="ARTESCA_Object_Management_Project_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0F294A")      # Navy Blue
    SECONDARY = colors.HexColor("#1D4ED8")    # Royal Blue
    ACCENT = colors.HexColor("#0284C7")       # Cyan/Blue Accent
    DARK = colors.HexColor("#0F172A")         # Slate 900
    MUTED = colors.HexColor("#475569")        # Slate 600
    BORDER = colors.HexColor("#CBD5E1")       # Border Gray
    BG_LIGHT = colors.HexColor("#F8FAFC")     # Light Slate
    BG_ACCENT = colors.HexColor("#EFF6FF")    # Light Blue

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=PRIMARY,
        alignment=0,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceAfter=25
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=DARK,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6
    )

    meta_label = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=PRIMARY
    )

    meta_val = ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=DARK
    )

    story = []

    # =========================================================================
    # COVER / TITLE BLOCK
    # =========================================================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("PROJECT DOCUMENTATION & TECHNICAL REPORT", ParagraphStyle('Eyebrow', fontName='Helvetica-Bold', fontSize=10, textColor=ACCENT, spaceAfter=8)))
    story.append(Paragraph("Scality ARTESCA S3 Object Storage Management & Searchable Metadata Catalog", title_style))
    story.append(Paragraph("An Enterprise Platform for Cloud Blob Storage, Visual Boolean AST Querying, Native PostgreSQL JSONB Indexing, and Schema Enforcement", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY, spaceAfter=15))

    meta_data = [
        [Paragraph("Project Name:", meta_label), Paragraph("Scality ARTESCA Object Management System", meta_val),
         Paragraph("Target Environment:", meta_label), Paragraph("Production & Air-Gapped Offline (DRDO)", meta_val)],
        [Paragraph("Author / Developer:", meta_label), Paragraph("Madhavi (DRDO Research Fellow)", meta_val),
         Paragraph("Architecture:", meta_label), Paragraph("FastAPI + React 19 + PostgreSQL 16 + S3", meta_val)],
        [Paragraph("Version:", meta_label), Paragraph("1.0.0 (Hardened & Verified)", meta_val),
         Paragraph("Verification Status:", meta_label), Paragraph("100% Tests Passed (S3 & Backend Engine)", meta_val)],
        [Paragraph("Storage Protocol:", meta_label), Paragraph("S3v4 / AWS Signature V4 REST API", meta_val),
         Paragraph("Database Engine:", meta_label), Paragraph("PostgreSQL JSONB + GIN Indexing", meta_val)],
    ]
    meta_table = Table(meta_data, colWidths=[110, 150, 110, 134])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # =========================================================================
    # EXECUTIVE SUMMARY / WHAT IS THE PROJECT?
    # =========================================================================
    story.append(Paragraph("1. Executive Summary & What is the Project?", h1_style))
    story.append(Paragraph(
        "Modern aerospace, defense, and high-assurance enterprise systems generate petabytes of unstructured files—including "
        "sensor logs, radar telemetry, engineering specifications, simulation models, and satellite imagery. While Scality ARTESCA "
        "and Amazon S3 provide virtually limitless, distributed blob storage, native S3 interfaces present severe operational limits "
        "when applied to enterprise discovery: <b>S3 cannot search user-defined metadata across an entire bucket without performing expensive, "
        "linear bucket traversals (ListObjectsV2)</b>, lacks multi-attribute boolean filtering, and offers no integrated schema validation.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Solution:</b> The <b>ARTESCA Object Management System</b> solves this fundamental problem by decoupling the "
        "<b>Storage Data Plane</b> (the raw binary payload persisted durably in Scality ARTESCA S3 storage) from the <b>Metadata Control Plane</b> "
        "(a relational catalog in PostgreSQL backed by native <code>JSONB</code> GIN indexing, visual boolean query execution, and enforced typed schemas). "
        "This architecture empowers users to search millions of objects in sub-millisecond query time using complex boolean logic without ever scanning S3 buckets directly.",
        body_style
    ))

    # System Architecture Highlights Table
    arch_highlights = [
        [Paragraph("Architectural Layer", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
         Paragraph("Technology Stack", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
         Paragraph("Core Responsibility & Implementation Details", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white))],
        [Paragraph("<b>Storage Data Plane</b>", body_style), Paragraph("Scality ARTESCA S3 / SeaweedFS S3", body_style),
         Paragraph("Persists raw object binaries; enforces S3v4 signature verification and streaming multi-part byte streaming.", body_style)],
        [Paragraph("<b>Metadata Catalog Plane</b>", body_style), Paragraph("PostgreSQL 14+ / JSONB + GIN", body_style),
         Paragraph("Provides ACID transactional persistence, relational foreign keys, and sub-millisecond GIN indexing over custom attributes.", body_style)],
        [Paragraph("<b>Application & API Tier</b>", body_style), Paragraph("FastAPI (Python 3.12) • Uvicorn", body_style),
         Paragraph("High-performance ASGI microservices; executes recursive AST query compilation, Argon2id security, JWT auth, and audit logging.", body_style)],
        [Paragraph("<b>Presentation Tier</b>", body_style), Paragraph("React 19 • TypeScript • Vite", body_style),
         Paragraph("Single-page interface featuring an interactive Visual AND/OR/NOT Query Builder, schema designer, and live validation sandbox.", body_style)],
    ]
    t_arch = Table(arch_highlights, colWidths=[120, 140, 244])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 15))

    # =========================================================================
    # WHAT I DID FROM START TO END (CHRONOLOGICAL JOURNEY)
    # =========================================================================
    story.append(Paragraph("2. Project Journey: What Was Done From Start to End", h1_style))
    story.append(Paragraph(
        "The project was executed through a systematic, multi-phase engineering methodology. Below is the complete chronological record of all "
        "work done, from initial architectural planning to final deployment hardening:",
        body_style
    ))

    phases = [
        ("Phase 1: Storage Layer Architecture & Scality S3 Connectivity", [
            "Configured Scality ARTESCA S3 storage connectivity using Python <b>Boto3</b> with Amazon S3 Signature Version 4 (s3v4).",
            "Deployed and configured a local high-performance S3 emulator (<b>SeaweedFS</b>) running on port 8333 to enable development and 100% offline air-gapped testing.",
            "Engineered zero-buffering object streaming routines (<code>s3_client.put_object</code> and <code>s3_client.get_object</code>) to eliminate RAM bottlenecks when uploading or downloading multi-gigabyte files.",
            "Wrote comprehensive diagnostic tooling (<code>test_artesca_s3.py</code>) to validate IAM access keys, bucket creation, PUT, GET bit-for-bit integrity, and DELETE operations."
        ]),
        ("Phase 2: Relational Metadata Database & PostgreSQL JSONB Engine", [
            "Designed a normalized relational database schema (<code>users</code>, <code>roles</code>, <code>permissions</code>, <code>objects</code>, <code>object_metadata</code>, <code>metadata_schemas</code>, <code>audit_events</code>).",
            "Configured <b>SQLAlchemy 2.0</b> alongside <b>Psycopg 3</b> with modern connection pooling, type annotations, and session management.",
            "Implemented the <code>custom_metadata</code> column in PostgreSQL using native <code>JSONB</code> type for semi-structured document tags.",
            "Engineered and executed an Alembic database migration (<code>b81a4d93e120_schemas_and_jsonb_indexing.py</code>) creating the specialized GIN index: "
            "<code>CREATE INDEX ix_object_metadata_custom_metadata_gin ON public.object_metadata USING gin (custom_metadata);</code>"
        ]),
        ("Phase 3: Core API Services, RBAC & Immutable Audit Trail", [
            "Constructed asynchronous REST API endpoints in <b>FastAPI</b> covering authentication, object lifecycle, metadata updates, search, and audit telemetry.",
            "Implemented military-grade password hashing using <b>Argon2id</b> (resistant to GPU/ASIC cracking) and stateless cryptographically signed <b>JWT bearer tokens</b>.",
            "Created fine-grained Role-Based Access Control (RBAC) enforced via Python decorators (<code>@require_permission</code>).",
            "Built an automated compensation mechanism: If database cataloging fails after an S3 upload, the system automatically rolls back and cleans up the orphan S3 object.",
            "Logged every storage mutation and catalog query into an immutable <code>audit_events</code> table recording timestamp, username, IP, action, and JSON payload."
        ]),
        ("Phase 4: Metadata Schema Administration & Dynamic Field Validation", [
            "Built the <code>MetadataSchema</code> model enabling administrators to define, version, and manage typed document schemas.",
            "Supported rich field data types: <code>string</code>, <code>number</code>, <code>boolean</code>, <code>date</code>, and <code>enum</code> (with discrete option lists).",
            "Engineered a dynamic validation engine (<code>/api/v1/schemas/{id}/validate</code>) validating arbitrary JSON payloads against schema rules.",
            "Developed an interactive <b>Validation Sandbox UI</b> in React allowing administrators to test and debug JSON metadata before saving.",
            "Integrated dynamic form generation into the Object Upload workflow, dynamically rendering required/optional inputs based on the chosen schema."
        ]),
        ("Phase 5: Visual AND/OR/NOT Query Builder & Recursive AST Compiler", [
            "Developed an Abstract Syntax Tree (AST) search model supporting recursive nested condition groups (AND, OR, NOT combinators).",
            "Implemented backend AST translation (<code>/api/v1/search/query</code>) generating safe, parameterized PostgreSQL SQL queries without injection risk.",
            "Created native PostgreSQL JSONB operator compilers: extracting text via <code>->></code>, verifying key existence via <code>?</code>, and evaluating numeric comparisons.",
            "Built a drag-and-drop Visual Query Builder UI with dynamic field pickers, type-specific operators, and tree-structure visual nesting lines."
        ]),
        ("Phase 6: Frontend Development & Design System Polish", [
            "Engineered a responsive single-page application using <b>React 19</b>, <b>TypeScript</b>, and <b>Vite</b>.",
            "Constructed a cohesive enterprise design system using Vanilla CSS tokens (dark-mode ready, glassmorphism, micro-animations).",
            "Built key interactive views: <b>Dashboard</b> (KPI cards, storage meters), <b>Objects & Search</b> (table viewer, visual query toggle), <b>Upload</b>, <b>Schemas</b>, and <b>Audit Trail</b>.",
            "Fixed layout discrepancies: Replaced unstyled Bootstrap classes with a responsive 3-column CSS Grid (<code>.feature-grid</code>) and standardized navigation labels."
        ]),
        ("Phase 7: Production Deployment Automation & Air-Gapped Packaging", [
            "Authored multi-stage <code>Dockerfile</code> compiling Vite assets in Node 20 and serving them directly via Python 3.12 FastAPI.",
            "Constructed <code>docker-compose.yml</code> orchestrating PostgreSQL, S3 storage, and the unified ARTESCA application container.",
            "Wrote systemd unit file (<code>artesca.service</code>) configured for high-concurrency multi-worker Uvicorn (<code>--workers 4</code>).",
            "Developed automated production deployment scripts: <code>deploy.sh</code>, <code>start_production.sh</code>, and <code>setup_offline.sh</code>.",
            "Prepared a 100% self-contained offline packaging strategy with pre-downloaded Python wheels in <code>backend/wheels/</code> and a complete database seed (<code>database_seed.sql</code>) for air-gapped DRDO systems."
        ]),
        ("Phase 8: Systematic Refinement & Scope Alignment", [
            "Audited the codebase against precise project constraints to remove all out-of-scope features.",
            "Eliminated pagination and server-side sorting envelopes to maintain direct array outputs.",
            "Removed bulk upload/bulk delete/bulk download code paths to focus on atomic single-object durability.",
            "Removed role administration UI and audit statistics dashboard, preserving a clean, focused compliance trail.",
            "Updated and verified test suites (<code>test_enhancements.py</code> and <code>test_artesca_s3.py</code>) achieving 100% pass rates."
        ])
    ]

    for title, items in phases:
        story.append(Paragraph(title, h2_style))
        for it in items:
            story.append(Paragraph(f"• {it}", bullet_style))
        story.append(Spacer(1, 4))

    # =========================================================================
    # DETAILED FEATURE SPECIFICATION
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Core Technical Features & Architecture", h1_style))
    story.append(Paragraph(
        "This section details the primary technical innovations engineered into the ARTESCA Object Management platform:",
        body_style
    ))

    story.append(Paragraph("A. Visual AND/OR/NOT Query Builder & AST Engine", h2_style))
    story.append(Paragraph(
        "Traditional S3 applications require users to know exact object keys or perform external database queries with rigid SQL. "
        "The ARTESCA Visual Query Builder introduces an <b>Abstract Syntax Tree (AST)</b> query model that allows analysts to construct "
        "deeply nested boolean expressions visually. The React component recursively renders condition groups connected by <b>AND</b> (all must match), "
        "<b>OR</b> (any may match), or <b>NOT</b> (negation).",
        body_style
    ))
    story.append(Paragraph("Sample AST Payload Transmitted to Backend (POST /api/v1/search/query):", ParagraphStyle('CodeLabel', fontName='Helvetica-Bold', fontSize=8, textColor=MUTED)))
    
    sample_ast = (
        '{\n'
        '  "root": {\n'
        '    "combinator": "AND",\n'
        '    "rules": [\n'
        '      {"field": "classification", "operator": "equals", "value": "RESTRICTED"},\n'
        '      {\n'
        '        "combinator": "OR",\n'
        '        "rules": [\n'
        '          {"field": "custom_metadata.radar_band", "operator": "equals", "value": "X-Band"},\n'
        '          {"field": "custom_metadata.frequency_ghz", "operator": ">=", "value": 9.2}\n'
        '        ]\n'
        '      },\n'
        '      {\n'
        '        "combinator": "NOT",\n'
        '        "rules": [\n'
        '          {"field": "filename", "operator": "contains", "value": "deprecated"}\n'
        '        ]\n'
        '      }\n'
        '    ]\n'
        '  }\n'
        '}'
    )
    t_code = Table([[Paragraph(f"<pre>{sample_ast}</pre>", code_style)]], colWidths=[504])
    t_code.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_code)
    story.append(Spacer(1, 8))

    story.append(Paragraph("B. Native PostgreSQL JSONB Querying & GIN Indexing", h2_style))
    story.append(Paragraph(
        "To achieve sub-millisecond search across arbitrary custom attributes without schema alter migrations, metadata is persisted "
        "in PostgreSQL's binary JSON format (<code>JSONB</code>). Unlike standard text JSON, <code>JSONB</code> decomposes keys and values "
        "into binary tokens and is fully indexable using Generalized Inverted Indexes (GIN).",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Index Definition:</b> <code>CREATE INDEX ix_object_metadata_custom_metadata_gin ON public.object_metadata USING gin (custom_metadata);</code><br/>"
        "• <b>Dialect-Aware Safe SQL:</b> Text fields are extracted using <code>custom_metadata ->> 'key'</code>; key presence is verified via the <code>?</code> operator; "
        "numeric comparisons cast values on-the-fly (<code>CAST(custom_metadata ->> 'freq' AS NUMERIC) >= 9.0</code>) with strict parameter binding to prevent SQL injection.",
        body_style
    ))

    story.append(Paragraph("C. Metadata Schema Administration & Validation Sandbox", h2_style))
    story.append(Paragraph(
        "Unstructured metadata often leads to data drift and inconsistent naming (e.g. <code>dept</code> vs <code>department</code>). "
        "The Schema Administration subsystem enforces typed governance templates before files reach storage. Schemas define required fields, "
        "data types (string, number, boolean, date), and discrete enumerated options (e.g., <code>['RADAR', 'LIDAR', 'THERMAL']</code>). "
        "The frontend upload view dynamically reads the active schema and automatically renders the appropriate form controls.",
        body_style
    ))

    # =========================================================================
    # DATABASE SCHEMA SPECIFICATION
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Relational Database Schema & Data Dictionary", h1_style))
    story.append(Paragraph("The system utilizes 7 relational tables designed for ACID transactionality and auditability:", body_style))

    db_tables = [
        [Paragraph("Table Name", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
         Paragraph("Primary Keys & Constraints", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white)),
         Paragraph("Description & Strategic Role", ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.white))],
        [Paragraph("<code>users</code>", body_style), Paragraph("id (PK), username (UQ)", body_style),
         Paragraph("Stores user identities, departments, and Argon2id password hashes.", body_style)],
        [Paragraph("<code>roles</code>", body_style), Paragraph("id (PK), name (UQ)", body_style),
         Paragraph("RBAC role definitions (ADMIN, EDITOR, USER, AUDITOR).", body_style)],
        [Paragraph("<code>permissions</code>", body_style), Paragraph("id (PK), name (UQ)", body_style),
         Paragraph("Atomic security permissions (OBJECT_UPLOAD, SCHEMA_WRITE, etc.).", body_style)],
        [Paragraph("<code>objects</code>", body_style), Paragraph("id (PK), object_key (UQ)", body_style),
         Paragraph("Tracks S3 storage objects: bucket, key, filename, size_bytes, content_type.", body_style)],
        [Paragraph("<code>object_metadata</code>", body_style), Paragraph("id (PK), object_id (FK, UQ)", body_style),
         Paragraph("Relational catalog attributes (classification, project) + JSONB custom_metadata.", body_style)],
        [Paragraph("<code>metadata_schemas</code>", body_style), Paragraph("id (PK), name (UQ)", body_style),
         Paragraph("Document schemas with JSON-encoded field definitions, types, and versioning.", body_style)],
        [Paragraph("<code>audit_events</code>", body_style), Paragraph("id (PK), timestamp (IDX)", body_style),
         Paragraph("Append-only immutable audit log recording every user and system operation.", body_style)],
    ]
    t_db = Table(db_tables, colWidths=[120, 140, 244])
    t_db.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_db)

    # =========================================================================
    # WHAT TO DO MORE / FUTURE ROADMAP
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("5. Future Roadmap & What to Do More", h1_style))
    story.append(Paragraph(
        "While the current system provides a robust, production-hardened platform for S3 storage management and metadata discovery, "
        "enterprise systems evolve continuously. Below is the recommended engineering roadmap outlining high-value future enhancements:",
        body_style
    ))

    roadmap_items = [
        ("1. Automated Metadata Extraction & AI Indexing Engine", [
            "<b>Optical Character Recognition (OCR):</b> Integrate Tesseract OCR or EasyOCR to extract searchable full-text metadata from scanned engineering drawings, PDF reports, and TIFF telemetry diagrams automatically upon upload.",
            "<b>EXIF & Media Metadata Extraction:</b> Automatically parse metadata headers from imagery (sensor coordinates, camera make, focal length) and geospatial data (GeoTIFF, NetCDF) into structured JSONB attributes.",
            "<b>Semantic Vector Search:</b> Embed a lightweight transformer model (such as all-MiniLM-L6-v2) using the PostgreSQL <code>pgvector</code> extension to enable natural-language semantic similarity search alongside boolean keyword queries."
        ]),
        ("2. S3 Object Lifecycle Management & WORM Retention Locks", [
            "<b>Automated Tiering Policies:</b> Configure S3 lifecycle rules transitioning aged objects (>90 days) from high-speed SSD storage to Scality cold-tier or tape archive storage while retaining instant searchability in the PostgreSQL catalog.",
            "<b>WORM Compliance (Write Once, Read Many):</b> Implement S3 Object Lock in Compliance Mode to prevent accidental or malicious deletion of mission-critical defense records prior to a legally mandated retention expiry date.",
            "<b>Multi-Version Concurrency:</b> Enable native S3 versioning with catalog tracking, allowing engineers to inspect, download, or roll back to historical iterations of modified documents."
        ]),
        ("3. Enterprise Identity Federation & Single Sign-On (SSO)", [
            "<b>OIDC / SAML 2.0 Integration:</b> Connect authentication to enterprise identity providers (Keycloak, Active Directory, FreeIPA, or Okta) via OpenID Connect (OIDC) or SAML 2.0.",
            "<b>Mutual TLS (mTLS):</b> Enforce certificate-based mutual authentication for machine-to-machine microservice communication in zero-trust networks.",
            "<b>Session Revocation Ledger:</b> Implement a Redis-backed token blacklist enabling instantaneous global session invalidation when administrative privileges are modified."
        ]),
        ("4. High Availability, Replication & Geo-Distribution", [
            "<b>Cross-Region S3 Replication (CRR):</b> Configure active-passive or active-active bucket replication across geographically separated DRDO data centers.",
            "<b>PostgreSQL Streaming Replication:</b> Deploy patroni-managed PostgreSQL cluster with hot standby read replicas to scale read-heavy catalog search queries horizontally.",
            "<b>Distributed Caching:</b> Cache frequent schema definitions and top queries in an in-memory Redis cluster with pub/sub cache invalidation."
        ]),
        ("5. Event-Driven Webhooks & Asynchronous Processing Pipeline", [
            "<b>Storage Event Notifications:</b> Publish S3 storage events (ObjectCreated, ObjectRemoved) to an enterprise message broker (Apache Kafka or RabbitMQ).",
            "<b>Background Asynchronous Workers:</b> Implement Celery or ARQ background workers to handle CPU-intensive tasks (virus scanning with ClamAV, file compression, format transcoding) asynchronously without blocking HTTP request threads.",
            "<b>Real-Time UI Updates:</b> Integrate WebSockets or Server-Sent Events (SSE) so users see newly indexed files and storage quota updates instantly on their dashboard."
        ]),
        ("6. Cryptographic Integrity & Tamper-Evident Signatures", [
            "<b>Content-Addressable Verification:</b> Compute cryptographic checksums (SHA-256 or BLAKE3) client-side before streaming and verify against server-computed hashes to guarantee bit-level data integrity.",
            "<b>Digital Watermarking & Signing:</b> Apply cryptographic digital signatures to exported records and sensitive technical documents before dissemination."
        ])
    ]

    for title, points in roadmap_items:
        story.append(Paragraph(title, h2_style))
        for p in points:
            story.append(Paragraph(f"• {p}", bullet_style))
        story.append(Spacer(1, 4))

    # =========================================================================
    # DEPLOYMENT & AIR-GAPPED TRANSFER INSTRUCTIONS
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("6. Operational Runbook & Air-Gapped Transfer Guide", h1_style))
    story.append(Paragraph(
        "For transferring and operating the platform in air-gapped defense environments (e.g. offline Ubuntu workstations at DRDO without internet access), "
        "follow this step-by-step runbook:",
        body_style
    ))

    runbook_steps = [
        "<b>Step 1: Archive Packaging on Internet-Connected Machine</b><br/>"
        "All Python wheels are pre-cached in <code>backend/wheels/</code>, the frontend distribution is pre-compiled in <code>frontend/dist/</code>, "
        "and SeaweedFS binary is included. Create an archive using: <code>zip -r artesca-object-management.zip artesca-object-management/</code>.",
        "<b>Step 2: Transfer Archive via Authorized Removable Media</b><br/>"
        "Transfer the zip file to the target offline machine and extract: <code>unzip artesca-object-management.zip && cd artesca-object-management</code>.",
        "<b>Step 3: Execute Automated Offline Setup</b><br/>"
        "Run the bundled offline setup script: <code>chmod +x setup_offline.sh deploy.sh start_production.sh && ./setup_offline.sh</code>.<br/>"
        "This script automatically restores the database seed (<code>database_seed.sql</code>), sets up the Python virtual environment using the local wheel cache, and configures storage.",
        "<b>Step 4: Launch Production Multi-Worker Server</b><br/>"
        "Start the application: <code>./start_production.sh</code>.<br/>"
        "The application is accessible immediately at <b>http://localhost:8000</b>. Default admin credentials: <code>madhavi</code> / <code>Madhavi@123</code>.",
        "<b>Step 5: Optional Systemd Service Installation</b><br/>"
        "To enable automatic startup on boot, copy the systemd unit: <code>sudo cp artesca.service /etc/systemd/system/ && sudo systemctl enable --now artesca.service</code>."
    ]

    for s in runbook_steps:
        story.append(Paragraph(s, bullet_style))
        story.append(Spacer(1, 3))

    # =========================================================================
    # CONCLUSION & SIGN-OFF BLOCK
    # =========================================================================
    story.append(Spacer(1, 15))
    story.append(Paragraph("7. Conclusion", h1_style))
    story.append(Paragraph(
        "The Scality ARTESCA Object Management System successfully overcomes native S3 metadata limitations through a decoupled, "
        "high-assurance architecture. By combining durable S3 object persistence with PostgreSQL JSONB indexing, visual boolean query compilation, "
        "enforced typed schemas, and comprehensive audit telemetry, the system provides a robust, enterprise-grade solution ready for immediate "
        "operational deployment in mission-critical environments.",
        body_style
    ))
    story.append(Spacer(1, 10))

    signoff_data = [
        [Paragraph("<b>Prepared by:</b>", meta_label), Paragraph("Madhavi (Project Developer)", meta_val),
         Paragraph("<b>Date of Completion:</b>", meta_label), Paragraph("October 2026", meta_val)],
        [Paragraph("<b>Platform Status:</b>", meta_label), Paragraph("Production & Offline Verified", meta_val),
         Paragraph("<b>Classification:</b>", meta_label), Paragraph("RESTRICTED / DEFENSE INTERNAL", meta_val)],
    ]
    t_signoff = Table(signoff_data, colWidths=[110, 150, 120, 124])
    t_signoff.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_ACCENT),
        ('BOX', (0,0), (-1,-1), 1, SECONDARY),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_signoff)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF documentation: {filename}")

if __name__ == "__main__":
    out_pdf = "/home/madhavi/projects/artesca-object-management/ARTESCA_Object_Management_Project_Documentation.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    create_pdf(out_pdf)
