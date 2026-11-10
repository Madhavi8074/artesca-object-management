--
-- PostgreSQL database dump
--

\restrict QvoV8hSvt362mGDIXQXdldeMW8cc15dGqbcXry1Jatyfzq3GSGXx3oRco6fQi0H

-- Dumped from database version 18.6 (Ubuntu 18.6-0ubuntu0.26.04.1)
-- Dumped by pg_dump version 18.6 (Ubuntu 18.6-0ubuntu0.26.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.user_roles DROP CONSTRAINT IF EXISTS user_roles_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_roles DROP CONSTRAINT IF EXISTS user_roles_role_id_fkey;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS role_permissions_role_id_fkey;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS role_permissions_permission_id_fkey;
ALTER TABLE IF EXISTS ONLY public.objects DROP CONSTRAINT IF EXISTS objects_owner_id_fkey;
ALTER TABLE IF EXISTS ONLY public.object_metadata DROP CONSTRAINT IF EXISTS object_metadata_object_id_fkey;
ALTER TABLE IF EXISTS ONLY public.object_metadata DROP CONSTRAINT IF EXISTS fk_object_metadata_schema_id;
ALTER TABLE IF EXISTS ONLY public.audit_events DROP CONSTRAINT IF EXISTS audit_events_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_events DROP CONSTRAINT IF EXISTS audit_events_object_id_fkey;
DROP INDEX IF EXISTS public.ix_users_username;
DROP INDEX IF EXISTS public.ix_roles_name;
DROP INDEX IF EXISTS public.ix_permissions_name;
DROP INDEX IF EXISTS public.ix_objects_status;
DROP INDEX IF EXISTS public.ix_objects_bucket;
DROP INDEX IF EXISTS public.ix_object_metadata_schema_id;
DROP INDEX IF EXISTS public.ix_object_metadata_project;
DROP INDEX IF EXISTS public.ix_object_metadata_object_id;
DROP INDEX IF EXISTS public.ix_object_metadata_document_type;
DROP INDEX IF EXISTS public.ix_object_metadata_department;
DROP INDEX IF EXISTS public.ix_object_metadata_custom_metadata_gin;
DROP INDEX IF EXISTS public.ix_object_metadata_classification;
DROP INDEX IF EXISTS public.ix_metadata_schemas_name;
DROP INDEX IF EXISTS public.ix_audit_events_user_id;
DROP INDEX IF EXISTS public.ix_audit_events_timestamp;
DROP INDEX IF EXISTS public.ix_audit_events_object_id;
DROP INDEX IF EXISTS public.ix_audit_events_action;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.user_roles DROP CONSTRAINT IF EXISTS user_roles_pkey;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS roles_pkey;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS role_permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.objects DROP CONSTRAINT IF EXISTS objects_pkey;
ALTER TABLE IF EXISTS ONLY public.object_metadata DROP CONSTRAINT IF EXISTS object_metadata_pkey;
ALTER TABLE IF EXISTS ONLY public.metadata_schemas DROP CONSTRAINT IF EXISTS metadata_schemas_pkey;
ALTER TABLE IF EXISTS ONLY public.audit_events DROP CONSTRAINT IF EXISTS audit_events_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.roles ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.permissions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.objects ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.object_metadata ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.metadata_schemas ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.audit_events ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.user_roles;
DROP SEQUENCE IF EXISTS public.roles_id_seq;
DROP TABLE IF EXISTS public.roles;
DROP TABLE IF EXISTS public.role_permissions;
DROP SEQUENCE IF EXISTS public.permissions_id_seq;
DROP TABLE IF EXISTS public.permissions;
DROP SEQUENCE IF EXISTS public.objects_id_seq;
DROP TABLE IF EXISTS public.objects;
DROP SEQUENCE IF EXISTS public.object_metadata_id_seq;
DROP TABLE IF EXISTS public.object_metadata;
DROP SEQUENCE IF EXISTS public.metadata_schemas_id_seq;
DROP TABLE IF EXISTS public.metadata_schemas;
DROP SEQUENCE IF EXISTS public.audit_events_id_seq;
DROP TABLE IF EXISTS public.audit_events;
DROP TABLE IF EXISTS public.alembic_version;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: artesca_app
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO artesca_app;

--
-- Name: audit_events; Type: TABLE; Schema: public; Owner: artesca_app
--

CREATE TABLE public.audit_events (
    id integer NOT NULL,
    user_id integer,
    action character varying(100) NOT NULL,
    object_id integer,
    resource_type character varying(100),
    resource_id character varying(255),
    "timestamp" timestamp with time zone NOT NULL,
    source_ip character varying(64),
    success boolean NOT NULL,
    error_code character varying(100),
    details json
);


ALTER TABLE public.audit_events OWNER TO artesca_app;

--
-- Name: audit_events_id_seq; Type: SEQUENCE; Schema: public; Owner: artesca_app
--

CREATE SEQUENCE public.audit_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_events_id_seq OWNER TO artesca_app;

--
-- Name: audit_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: artesca_app
--

ALTER SEQUENCE public.audit_events_id_seq OWNED BY public.audit_events.id;


--
-- Name: metadata_schemas; Type: TABLE; Schema: public; Owner: artesca_app
--

CREATE TABLE public.metadata_schemas (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    version character varying(20) DEFAULT '1.0'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    fields jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.metadata_schemas OWNER TO artesca_app;

--
-- Name: metadata_schemas_id_seq; Type: SEQUENCE; Schema: public; Owner: artesca_app
--

CREATE SEQUENCE public.metadata_schemas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.metadata_schemas_id_seq OWNER TO artesca_app;

--
-- Name: metadata_schemas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: artesca_app
--

ALTER SEQUENCE public.metadata_schemas_id_seq OWNED BY public.metadata_schemas.id;


--
-- Name: object_metadata; Type: TABLE; Schema: public; Owner: artesca_app
--

CREATE TABLE public.object_metadata (
    id integer NOT NULL,
    object_id integer NOT NULL,
    classification character varying(100),
    department character varying(200),
    project character varying(200),
    document_type character varying(100),
    author character varying(200),
    description text,
    custom_metadata jsonb,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    schema_id integer
);


ALTER TABLE public.object_metadata OWNER TO artesca_app;

--
-- Name: object_metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: artesca_app
--

CREATE SEQUENCE public.object_metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.object_metadata_id_seq OWNER TO artesca_app;

--
-- Name: object_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: artesca_app
--

ALTER SEQUENCE public.object_metadata_id_seq OWNED BY public.object_metadata.id;


--
-- Name: objects; Type: TABLE; Schema: public; Owner: artesca_app
--

CREATE TABLE public.objects (
    id integer NOT NULL,
    bucket character varying(255) NOT NULL,
    object_key text NOT NULL,
    filename character varying(500) NOT NULL,
    content_type character varying(255),
    size_bytes bigint NOT NULL,
    etag character varying(255),
    version_id character varying(255),
    owner_id integer,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.objects OWNER TO artesca_app;

--
-- Name: objects_id_seq; Type: SEQUENCE; Schema: public; Owner: artesca_app
--

CREATE SEQUENCE public.objects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.objects_id_seq OWNER TO artesca_app;

--
-- Name: objects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: artesca_app
--

ALTER SEQUENCE public.objects_id_seq OWNED BY public.objects.id;


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: artesca_app
--

CREATE TABLE public.permissions (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text
);


ALTER TABLE public.permissions OWNER TO artesca_app;

--
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: artesca_app
--

CREATE SEQUENCE public.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.permissions_id_seq OWNER TO artesca_app;

--
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: artesca_app
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: artesca_app
--

CREATE TABLE public.role_permissions (
    role_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.role_permissions OWNER TO artesca_app;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: artesca_app
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text
);


ALTER TABLE public.roles OWNER TO artesca_app;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: artesca_app
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_seq OWNER TO artesca_app;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: artesca_app
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: artesca_app
--

CREATE TABLE public.user_roles (
    user_id integer NOT NULL,
    role_id integer NOT NULL
);


ALTER TABLE public.user_roles OWNER TO artesca_app;

--
-- Name: users; Type: TABLE; Schema: public; Owner: artesca_app
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    display_name character varying(200),
    email character varying(320),
    department character varying(200),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    password_hash character varying(255)
);


ALTER TABLE public.users OWNER TO artesca_app;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: artesca_app
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO artesca_app;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: artesca_app
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: audit_events id; Type: DEFAULT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.audit_events ALTER COLUMN id SET DEFAULT nextval('public.audit_events_id_seq'::regclass);


--
-- Name: metadata_schemas id; Type: DEFAULT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.metadata_schemas ALTER COLUMN id SET DEFAULT nextval('public.metadata_schemas_id_seq'::regclass);


--
-- Name: object_metadata id; Type: DEFAULT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.object_metadata ALTER COLUMN id SET DEFAULT nextval('public.object_metadata_id_seq'::regclass);


--
-- Name: objects id; Type: DEFAULT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.objects ALTER COLUMN id SET DEFAULT nextval('public.objects_id_seq'::regclass);


--
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: artesca_app
--

COPY public.alembic_version (version_num) FROM stdin;
b81a4d93e120
\.


--
-- Data for Name: audit_events; Type: TABLE DATA; Schema: public; Owner: artesca_app
--

COPY public.audit_events (id, user_id, action, object_id, resource_type, resource_id, "timestamp", source_ip, success, error_code, details) FROM stdin;
2	\N	OBJECT_UPLOAD	\N	object	4	2026-10-02 13:10:07.322517+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/audit-upload.txt", "filename": "audit-upload.txt", "size_bytes": 18}
3	\N	OBJECT_DOWNLOAD	\N	object	4	2026-10-02 13:10:40.484363+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/audit-upload.txt", "filename": "audit-upload.txt"}
4	\N	OBJECT_DELETE	\N	object	4	2026-10-02 13:11:20.529889+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/audit-upload.txt", "filename": "audit-upload.txt"}
5	\N	OBJECT_UPLOAD	\N	object	5	2026-10-02 13:24:34.358976+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/final-audit-test.txt", "filename": "final-audit-test.txt", "size_bytes": 22}
6	\N	OBJECT_METADATA_UPDATE	\N	object	5	2026-10-02 13:24:44.680701+00	\N	t	\N	{"filename": "final-audit-test.txt", "bucket": "artesca-documents", "object_key": "uploads/final-audit-test.txt", "updated_fields": {"description": "Final audit metadata update", "custom_metadata": {"reviewed": "yes", "environment": "development"}}}
7	\N	OBJECT_DOWNLOAD	\N	object	5	2026-10-02 13:24:51.193146+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/final-audit-test.txt", "filename": "final-audit-test.txt"}
8	\N	OBJECT_DELETE	\N	object	5	2026-10-02 13:25:49.099106+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/final-audit-test.txt", "filename": "final-audit-test.txt"}
1	\N	OBJECT_METADATA_UPDATE	\N	object	3	2026-10-02 12:57:11.51953+00	\N	t	\N	{"filename": "update-test-final.txt", "bucket": "artesca-documents", "object_key": "uploads/update-test.txt", "updated_fields": {"description": "Audit logging test", "custom_metadata": {"reviewed": "yes", "audit_test": "true"}}}
9	\N	OBJECT_DELETE	\N	object	3	2026-10-03 04:03:50.680633+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/update-test.txt", "filename": "update-test-final.txt"}
10	\N	OBJECT_UPLOAD	\N	object	6	2026-10-03 04:12:35.736176+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/editor-test.txt", "filename": "final-test.txt", "size_bytes": 26}
11	\N	OBJECT_DOWNLOAD	\N	object	6	2026-10-03 04:14:00.095596+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/editor-test.txt", "filename": "final-test.txt"}
12	\N	OBJECT_METADATA_UPDATE	\N	object	6	2026-10-03 04:15:28.4409+00	\N	t	\N	{"filename": "final-test.txt", "bucket": "artesca-documents", "object_key": "uploads/editor-test.txt", "updated_fields": {"classification": "CONFIDENTIAL", "department": "Engineering", "project": "Artesca", "document_type": "TEST", "author": "Madhavi", "description": "Final metadata test", "custom_metadata": {"environment": "development", "reviewed": "yes"}}}
45	\N	OBJECT_DOWNLOAD	\N	object	6	2026-10-03 06:43:32.993563+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/editor-test.txt", "filename": "final-test.txt"}
46	\N	OBJECT_DELETE	\N	object	6	2026-10-03 06:43:58.074952+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/editor-test.txt", "filename": "final-test.txt"}
47	\N	OBJECT_UPLOAD	7	object	7	2026-10-03 06:53:30.89299+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/editor-final-project-test.txt", "filename": "final-project-test.txt", "size_bytes": 27}
48	\N	OBJECT_UPLOAD	8	object	8	2026-10-03 06:57:47.392831+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/admin-final-project-test.txt", "filename": "final-project-test.txt", "size_bytes": 27}
49	\N	OBJECT_DOWNLOAD	8	object	8	2026-10-03 06:58:49.311446+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/admin-final-project-test.txt", "filename": "final-project-test.txt"}
50	\N	OBJECT_METADATA_UPDATE	8	object	8	2026-10-03 06:59:08.853818+00	\N	t	\N	{"filename": "final-project-test.txt", "bucket": "artesca-documents", "object_key": "uploads/admin-final-project-test.txt", "updated_fields": {"classification": "CONFIDENTIAL", "department": "Engineering", "project": "Artesca", "document_type": "PROJECT_TEST", "author": "Madhavi", "description": "Final project verification", "custom_metadata": {"environment": "development", "verified": "yes"}}}
51	\N	OBJECT_UPLOAD	\N	object	9	2026-10-03 07:33:58.3838+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/tokens.txt", "filename": "tokens.txt", "size_bytes": 1210}
52	\N	OBJECT_DELETE	\N	object	9	2026-10-03 07:38:23.299293+00	\N	t	\N	{"bucket": "artesca-documents", "object_key": "uploads/tokens.txt", "filename": "tokens.txt"}
53	2	USER_LOGIN	\N	auth	madhavi	2026-10-04 03:54:52.768286+00	\N	t	\N	{"username": "madhavi"}
54	2	SCHEMA_CREATE	\N	schema	2	2026-10-04 03:54:52.913174+00	\N	t	\N	{"name": "Engineering Design Document", "field_count": 4}
55	2	USER_LOGIN	\N	auth	madhavi	2026-10-04 03:55:08.028358+00	\N	t	\N	{"username": "madhavi"}
56	2	USER_LOGIN	\N	auth	madhavi	2026-10-04 03:55:22.383567+00	\N	t	\N	{"username": "madhavi"}
57	2	SCHEMA_CREATE	\N	schema	3	2026-10-04 03:55:22.527108+00	\N	t	\N	{"name": "Engineering Design Document 1791086122", "field_count": 4}
58	2	USER_LOGIN	\N	auth	madhavi	2026-10-04 03:55:44.312484+00	\N	t	\N	{"username": "madhavi"}
59	2	SCHEMA_CREATE	\N	schema	4	2026-10-04 03:55:44.434615+00	\N	t	\N	{"name": "Engineering Design Document 1791086144", "field_count": 4}
60	2	OBJECT_UPLOAD	10	object	10	2026-10-04 03:55:44.581461+00	\N	t	\N	{"batch": true, "filename": "mission_alpha_telemetry.log", "object_key": "mission_alpha_telemetry.log", "size_bytes": 32}
61	2	OBJECT_UPLOAD	11	object	11	2026-10-04 03:55:44.64436+00	\N	t	\N	{"batch": true, "filename": "mission_bravo_telemetry.log", "object_key": "mission_bravo_telemetry.log", "size_bytes": 32}
62	2	USER_LOGIN	\N	auth	madhavi	2026-10-04 03:55:58.047692+00	\N	t	\N	{"username": "madhavi"}
63	2	SCHEMA_CREATE	\N	schema	5	2026-10-04 03:55:58.169684+00	\N	t	\N	{"name": "Engineering Design Document 1791086158", "field_count": 4}
64	2	OBJECT_UPLOAD	12	object	12	2026-10-04 03:55:58.303335+00	\N	t	\N	{"batch": true, "filename": "mission_alpha_telemetry.log", "object_key": "20261004035558_mission_alpha_telemetry.log", "size_bytes": 32}
65	2	OBJECT_UPLOAD	13	object	13	2026-10-04 03:55:58.349594+00	\N	t	\N	{"batch": true, "filename": "mission_bravo_telemetry.log", "object_key": "20261004035558_mission_bravo_telemetry.log", "size_bytes": 32}
66	2	USER_LOGIN	\N	auth	madhavi	2026-10-04 04:08:37.782038+00	\N	t	\N	{"username": "madhavi"}
67	2	SCHEMA_CREATE	\N	schema	6	2026-10-04 04:08:38.226309+00	\N	t	\N	{"name": "Engineering Design Document 1791086918", "field_count": 4}
68	2	OBJECT_UPLOAD	14	object	14	2026-10-04 04:08:38.575543+00	\N	t	\N	{"batch": true, "filename": "mission_alpha_telemetry.log", "object_key": "20261004040838_mission_alpha_telemetry.log", "size_bytes": 32}
69	2	OBJECT_UPLOAD	15	object	15	2026-10-04 04:08:38.696937+00	\N	t	\N	{"batch": true, "filename": "mission_bravo_telemetry.log", "object_key": "20261004040838_mission_bravo_telemetry.log", "size_bytes": 32}
70	2	USER_LOGIN	\N	auth	madhavi	2026-10-04 04:09:30.896258+00	\N	t	\N	{"username": "madhavi"}
71	2	SCHEMA_CREATE	\N	schema	7	2026-10-04 04:09:31.483627+00	\N	t	\N	{"name": "Engineering Design Document 1791086971", "field_count": 4}
72	2	OBJECT_UPLOAD	16	object	16	2026-10-04 04:09:31.77016+00	\N	t	\N	{"batch": true, "filename": "mission_alpha_telemetry.log", "object_key": "20261004040931_mission_alpha_telemetry.log", "size_bytes": 32}
73	2	OBJECT_UPLOAD	17	object	17	2026-10-04 04:09:31.863426+00	\N	t	\N	{"batch": true, "filename": "mission_bravo_telemetry.log", "object_key": "20261004040931_mission_bravo_telemetry.log", "size_bytes": 32}
74	2	USER_LOGIN	\N	auth	madhavi	2026-10-04 04:10:06.291141+00	\N	t	\N	{"username": "madhavi"}
75	2	SCHEMA_CREATE	\N	schema	8	2026-10-04 04:10:06.763261+00	\N	t	\N	{"name": "Engineering Design Document 1791087006", "field_count": 4}
76	2	OBJECT_UPLOAD	\N	object	18	2026-10-04 04:10:07.114496+00	\N	t	\N	{"batch": true, "filename": "mission_alpha_telemetry.log", "object_key": "20261004041007_mission_alpha_telemetry.log", "size_bytes": 32}
78	2	OBJECT_DOWNLOAD	\N	object	18	2026-10-04 04:10:07.769057+00	\N	t	\N	{"batch_download": true, "filename": "mission_alpha_telemetry.log"}
80	2	OBJECT_DELETE	\N	object	18	2026-10-04 04:10:08.180356+00	\N	t	\N	{"batch_delete": true, "filename": "mission_alpha_telemetry.log", "object_key": "20261004041007_mission_alpha_telemetry.log"}
77	2	OBJECT_UPLOAD	\N	object	19	2026-10-04 04:10:07.258145+00	\N	t	\N	{"batch": true, "filename": "mission_bravo_telemetry.log", "object_key": "20261004041007_mission_bravo_telemetry.log", "size_bytes": 32}
79	2	OBJECT_DOWNLOAD	\N	object	19	2026-10-04 04:10:07.769066+00	\N	t	\N	{"batch_download": true, "filename": "mission_bravo_telemetry.log"}
81	2	OBJECT_DELETE	\N	object	19	2026-10-04 04:10:08.180364+00	\N	t	\N	{"batch_delete": true, "filename": "mission_bravo_telemetry.log", "object_key": "20261004041007_mission_bravo_telemetry.log"}
82	2	SCHEMA_DELETE	\N	schema	8	2026-10-04 04:10:08.261762+00	\N	t	\N	{"name": "Engineering Design Document 1791087006"}
83	2	USER_LOGIN	\N	auth	madhavi	2026-10-04 04:18:57.390709+00	\N	t	\N	{"username": "madhavi"}
84	2	SCHEMA_CREATE	\N	schema	9	2026-10-04 04:18:57.684134+00	\N	t	\N	{"name": "Engineering Design Document 1791087537", "field_count": 4}
85	2	OBJECT_UPLOAD	\N	object	20	2026-10-04 04:18:57.919002+00	\N	t	\N	{"batch": true, "filename": "mission_alpha_telemetry.log", "object_key": "20261004041857_mission_alpha_telemetry.log", "size_bytes": 32}
87	2	OBJECT_DOWNLOAD	\N	object	20	2026-10-04 04:18:58.28229+00	\N	t	\N	{"batch_download": true, "filename": "mission_alpha_telemetry.log"}
89	2	OBJECT_DELETE	\N	object	20	2026-10-04 04:18:58.611002+00	\N	t	\N	{"batch_delete": true, "filename": "mission_alpha_telemetry.log", "object_key": "20261004041857_mission_alpha_telemetry.log"}
86	2	OBJECT_UPLOAD	\N	object	21	2026-10-04 04:18:57.997082+00	\N	t	\N	{"batch": true, "filename": "mission_bravo_telemetry.log", "object_key": "20261004041857_mission_bravo_telemetry.log", "size_bytes": 32}
88	2	OBJECT_DOWNLOAD	\N	object	21	2026-10-04 04:18:58.282297+00	\N	t	\N	{"batch_download": true, "filename": "mission_bravo_telemetry.log"}
90	2	OBJECT_DELETE	\N	object	21	2026-10-04 04:18:58.611009+00	\N	t	\N	{"batch_delete": true, "filename": "mission_bravo_telemetry.log", "object_key": "20261004041857_mission_bravo_telemetry.log"}
91	2	SCHEMA_DELETE	\N	schema	9	2026-10-04 04:18:58.702236+00	\N	t	\N	{"name": "Engineering Design Document 1791087537"}
\.


--
-- Data for Name: metadata_schemas; Type: TABLE DATA; Schema: public; Owner: artesca_app
--

COPY public.metadata_schemas (id, name, description, version, is_active, fields, created_at, updated_at) FROM stdin;
1	Enterprise Document Schema	Standard enterprise document classification, retention, and department metadata	1.0	t	[{"name": "retention_years", "type": "number", "label": "Retention Period (Years)", "required": true, "max_value": 100, "min_value": 1, "default_value": 7}, {"name": "confidentiality_level", "type": "enum", "label": "Confidentiality Level", "options": ["Low", "Medium", "High", "Critical"], "required": true, "default_value": "Medium"}, {"name": "compliance_standard", "type": "string", "label": "Compliance Standard", "required": false, "default_value": "ISO-27001"}, {"name": "is_reviewed", "type": "boolean", "label": "Security Reviewed", "required": false, "default_value": false}]	2026-10-04 03:48:23.403212+00	2026-10-04 03:48:23.403218+00
2	Engineering Design Document	Schema for aerospace and defense engineering files	1.0	t	[{"name": "project_code", "type": "string", "label": "Project Code", "options": [], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "security_level", "type": "string", "label": "Security Level", "options": ["Unclassified", "Confidential", "Secret", "Top Secret"], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "revision", "type": "number", "label": "Revision Number", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "is_approved", "type": "boolean", "label": "Approval Status", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}]	2026-10-04 03:54:52.909042+00	2026-10-04 03:54:52.909047+00
3	Engineering Design Document 1791086122	Schema for aerospace and defense engineering files	1.0	t	[{"name": "project_code", "type": "string", "label": "Project Code", "options": [], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "security_level", "type": "string", "label": "Security Level", "options": ["Unclassified", "Confidential", "Secret", "Top Secret"], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "revision", "type": "number", "label": "Revision Number", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "is_approved", "type": "boolean", "label": "Approval Status", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}]	2026-10-04 03:55:22.524686+00	2026-10-04 03:55:22.524694+00
4	Engineering Design Document 1791086144	Schema for aerospace and defense engineering files	1.0	t	[{"name": "project_code", "type": "string", "label": "Project Code", "options": [], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "security_level", "type": "string", "label": "Security Level", "options": ["Unclassified", "Confidential", "Secret", "Top Secret"], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "revision", "type": "number", "label": "Revision Number", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "is_approved", "type": "boolean", "label": "Approval Status", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}]	2026-10-04 03:55:44.432517+00	2026-10-04 03:55:44.432522+00
5	Engineering Design Document 1791086158	Schema for aerospace and defense engineering files	1.0	t	[{"name": "project_code", "type": "string", "label": "Project Code", "options": [], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "security_level", "type": "string", "label": "Security Level", "options": ["Unclassified", "Confidential", "Secret", "Top Secret"], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "revision", "type": "number", "label": "Revision Number", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "is_approved", "type": "boolean", "label": "Approval Status", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}]	2026-10-04 03:55:58.166894+00	2026-10-04 03:55:58.166899+00
6	Engineering Design Document 1791086918	Schema for aerospace and defense engineering files	1.0	t	[{"name": "project_code", "type": "string", "label": "Project Code", "options": [], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "security_level", "type": "string", "label": "Security Level", "options": ["Unclassified", "Confidential", "Secret", "Top Secret"], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "revision", "type": "number", "label": "Revision Number", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "is_approved", "type": "boolean", "label": "Approval Status", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}]	2026-10-04 04:08:38.22045+00	2026-10-04 04:08:38.22046+00
7	Engineering Design Document 1791086971	Schema for aerospace and defense engineering files	1.0	t	[{"name": "project_code", "type": "string", "label": "Project Code", "options": [], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "security_level", "type": "string", "label": "Security Level", "options": ["Unclassified", "Confidential", "Secret", "Top Secret"], "required": true, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "revision", "type": "number", "label": "Revision Number", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}, {"name": "is_approved", "type": "boolean", "label": "Approval Status", "options": [], "required": false, "max_value": null, "min_value": null, "description": null, "default_value": null, "validation_regex": null}]	2026-10-04 04:09:31.477021+00	2026-10-04 04:09:31.477028+00
\.


--
-- Data for Name: object_metadata; Type: TABLE DATA; Schema: public; Owner: artesca_app
--

COPY public.object_metadata (id, object_id, classification, department, project, document_type, author, description, custom_metadata, created_at, updated_at, schema_id) FROM stdin;
1	1	INTERNAL	Engineering	Project-A	Technical Document	Madhavi	Updated project documentation	{"priority": "high", "review_status": "reviewed"}	2026-10-02 10:19:22.077676+00	2026-10-02 12:26:46.826632+00	\N
7	7	\N	\N	\N	\N	\N	\N	\N	2026-10-03 06:53:30.895489+00	2026-10-03 06:53:30.895492+00	\N
8	8	CONFIDENTIAL	Engineering	Artesca	PROJECT_TEST	Madhavi	Final project verification	{"verified": "yes", "environment": "development"}	2026-10-03 06:57:47.394712+00	2026-10-03 06:59:08.855816+00	\N
10	10	\N	\N	\N	\N	\N	\N	{"revision": 1, "project_code": "AERO-X1", "security_level": "Secret"}	2026-10-04 03:55:44.583663+00	2026-10-04 03:55:44.583667+00	4
11	11	\N	\N	\N	\N	\N	\N	{"revision": 1, "project_code": "AERO-X1", "security_level": "Secret"}	2026-10-04 03:55:44.648707+00	2026-10-04 03:55:44.648714+00	4
12	12	\N	\N	\N	\N	\N	\N	{"revision": 1, "project_code": "AERO-X1", "security_level": "Secret"}	2026-10-04 03:55:58.305821+00	2026-10-04 03:55:58.305826+00	5
13	13	\N	\N	\N	\N	\N	\N	{"revision": 1, "project_code": "AERO-X1", "security_level": "Secret"}	2026-10-04 03:55:58.350798+00	2026-10-04 03:55:58.350803+00	5
14	14	\N	\N	\N	\N	\N	\N	{"revision": 1, "project_code": "AERO-X1", "security_level": "Secret"}	2026-10-04 04:08:38.594536+00	2026-10-04 04:08:38.594546+00	6
15	15	\N	\N	\N	\N	\N	\N	{"revision": 1, "project_code": "AERO-X1", "security_level": "Secret"}	2026-10-04 04:08:38.699032+00	2026-10-04 04:08:38.69904+00	6
16	16	\N	\N	\N	\N	\N	\N	{"revision": 1, "project_code": "AERO-X1", "security_level": "Secret"}	2026-10-04 04:09:31.778032+00	2026-10-04 04:09:31.778042+00	7
17	17	\N	\N	\N	\N	\N	\N	{"revision": 1, "project_code": "AERO-X1", "security_level": "Secret"}	2026-10-04 04:09:31.871465+00	2026-10-04 04:09:31.871474+00	7
\.


--
-- Data for Name: objects; Type: TABLE DATA; Schema: public; Owner: artesca_app
--

COPY public.objects (id, bucket, object_key, filename, content_type, size_bytes, etag, version_id, owner_id, status, created_at, updated_at) FROM stdin;
1	documents	project-a/report.pdf	report.pdf	application/pdf	125000	\N	\N	\N	ACTIVE	2026-10-02 10:19:22.064495+00	2026-10-02 10:19:22.064502+00
7	artesca-documents	uploads/editor-final-project-test.txt	final-project-test.txt	text/plain	27	\N	\N	\N	ACTIVE	2026-10-03 06:53:30.8899+00	2026-10-03 06:53:30.889905+00
8	artesca-documents	uploads/admin-final-project-test.txt	final-project-test.txt	text/plain	27	\N	\N	\N	ACTIVE	2026-10-03 06:57:47.391482+00	2026-10-03 06:57:47.391487+00
10	artesca-documents	mission_alpha_telemetry.log	mission_alpha_telemetry.log	text/plain	32	\N	\N	2	ACTIVE	2026-10-04 03:55:44.575811+00	2026-10-04 03:55:44.575817+00
11	artesca-documents	mission_bravo_telemetry.log	mission_bravo_telemetry.log	text/plain	32	\N	\N	2	ACTIVE	2026-10-04 03:55:44.640675+00	2026-10-04 03:55:44.640679+00
12	artesca-documents	20261004035558_mission_alpha_telemetry.log	mission_alpha_telemetry.log	text/plain	32	\N	\N	2	ACTIVE	2026-10-04 03:55:58.300054+00	2026-10-04 03:55:58.300058+00
13	artesca-documents	20261004035558_mission_bravo_telemetry.log	mission_bravo_telemetry.log	text/plain	32	\N	\N	2	ACTIVE	2026-10-04 03:55:58.348211+00	2026-10-04 03:55:58.348216+00
14	artesca-documents	20261004040838_mission_alpha_telemetry.log	mission_alpha_telemetry.log	text/plain	32	\N	\N	2	ACTIVE	2026-10-04 04:08:38.571094+00	2026-10-04 04:08:38.571105+00
15	artesca-documents	20261004040838_mission_bravo_telemetry.log	mission_bravo_telemetry.log	text/plain	32	\N	\N	2	ACTIVE	2026-10-04 04:08:38.686797+00	2026-10-04 04:08:38.686818+00
16	artesca-documents	20261004040931_mission_alpha_telemetry.log	mission_alpha_telemetry.log	text/plain	32	\N	\N	2	ACTIVE	2026-10-04 04:09:31.762561+00	2026-10-04 04:09:31.762569+00
17	artesca-documents	20261004040931_mission_bravo_telemetry.log	mission_bravo_telemetry.log	text/plain	32	\N	\N	2	ACTIVE	2026-10-04 04:09:31.85897+00	2026-10-04 04:09:31.858979+00
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: artesca_app
--

COPY public.permissions (id, name, description) FROM stdin;
1	OBJECT_UPLOAD	Upload objects
2	OBJECT_READ	View object metadata
3	OBJECT_UPDATE	Update object metadata
4	OBJECT_DOWNLOAD	Download objects
5	OBJECT_DELETE	Delete objects
6	AUDIT_READ	View audit events
7	SCHEMA_READ	Read and list metadata schemas
8	SCHEMA_WRITE	Create, update, and delete metadata schemas
9	ROLE_ADMIN	Manage roles and permissions
10	USER_ADMIN	Manage users and assign roles
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: artesca_app
--

COPY public.role_permissions (role_id, permission_id) FROM stdin;
1	1
1	2
1	3
1	4
1	5
1	6
2	1
2	2
2	3
2	4
3	2
3	4
1	7
1	8
1	9
1	10
2	7
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: artesca_app
--

COPY public.roles (id, name, description) FROM stdin;
1	ADMIN	Full access to objects and audit logs
2	EDITOR	Create, view, update and download objects
3	VIEWER	View and download objects
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: artesca_app
--

COPY public.user_roles (user_id, role_id) FROM stdin;
2	1
3	2
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: artesca_app
--

COPY public.users (id, username, display_name, email, department, is_active, created_at, updated_at, password_hash) FROM stdin;
3	editor	Editor User	editor@example.com	Engineering	t	2026-10-03 00:07:34.207004+00	2026-10-03 00:15:52.282467+00	$argon2id$v=19$m=65536,t=3,p=4$vS6D9yacFZl9HkoHYw+1MQ$VFRnYoO+sNPlQYV4VHhGJ3+GOs9J92+hemPHVVKqUek
2	madhavi	Madhavi	madhavi@example.com	Engineering	t	2026-10-02 23:20:14.037723+00	2026-10-03 06:41:48.934455+00	$argon2id$v=19$m=65536,t=3,p=4$6r+jrLcpqyaF0NqwixO/ug$FXXskR2Vxq3Nh3ko9Ly6dY5Gov+0i++DfetIkv+ujtc
\.


--
-- Name: audit_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: artesca_app
--

SELECT pg_catalog.setval('public.audit_events_id_seq', 91, true);


--
-- Name: metadata_schemas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: artesca_app
--

SELECT pg_catalog.setval('public.metadata_schemas_id_seq', 9, true);


--
-- Name: object_metadata_id_seq; Type: SEQUENCE SET; Schema: public; Owner: artesca_app
--

SELECT pg_catalog.setval('public.object_metadata_id_seq', 21, true);


--
-- Name: objects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: artesca_app
--

SELECT pg_catalog.setval('public.objects_id_seq', 21, true);


--
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: artesca_app
--

SELECT pg_catalog.setval('public.permissions_id_seq', 10, true);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: artesca_app
--

SELECT pg_catalog.setval('public.roles_id_seq', 3, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: artesca_app
--

SELECT pg_catalog.setval('public.users_id_seq', 4, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_events audit_events_pkey; Type: CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_pkey PRIMARY KEY (id);


--
-- Name: metadata_schemas metadata_schemas_pkey; Type: CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.metadata_schemas
    ADD CONSTRAINT metadata_schemas_pkey PRIMARY KEY (id);


--
-- Name: object_metadata object_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.object_metadata
    ADD CONSTRAINT object_metadata_pkey PRIMARY KEY (id);


--
-- Name: objects objects_pkey; Type: CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.objects
    ADD CONSTRAINT objects_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_audit_events_action; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_audit_events_action ON public.audit_events USING btree (action);


--
-- Name: ix_audit_events_object_id; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_audit_events_object_id ON public.audit_events USING btree (object_id);


--
-- Name: ix_audit_events_timestamp; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_audit_events_timestamp ON public.audit_events USING btree ("timestamp");


--
-- Name: ix_audit_events_user_id; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_audit_events_user_id ON public.audit_events USING btree (user_id);


--
-- Name: ix_metadata_schemas_name; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE UNIQUE INDEX ix_metadata_schemas_name ON public.metadata_schemas USING btree (name);


--
-- Name: ix_object_metadata_classification; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_object_metadata_classification ON public.object_metadata USING btree (classification);


--
-- Name: ix_object_metadata_custom_metadata_gin; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_object_metadata_custom_metadata_gin ON public.object_metadata USING gin (custom_metadata);


--
-- Name: ix_object_metadata_department; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_object_metadata_department ON public.object_metadata USING btree (department);


--
-- Name: ix_object_metadata_document_type; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_object_metadata_document_type ON public.object_metadata USING btree (document_type);


--
-- Name: ix_object_metadata_object_id; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE UNIQUE INDEX ix_object_metadata_object_id ON public.object_metadata USING btree (object_id);


--
-- Name: ix_object_metadata_project; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_object_metadata_project ON public.object_metadata USING btree (project);


--
-- Name: ix_object_metadata_schema_id; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_object_metadata_schema_id ON public.object_metadata USING btree (schema_id);


--
-- Name: ix_objects_bucket; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_objects_bucket ON public.objects USING btree (bucket);


--
-- Name: ix_objects_status; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE INDEX ix_objects_status ON public.objects USING btree (status);


--
-- Name: ix_permissions_name; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);


--
-- Name: ix_roles_name; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: artesca_app
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: audit_events audit_events_object_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_object_id_fkey FOREIGN KEY (object_id) REFERENCES public.objects(id) ON DELETE SET NULL;


--
-- Name: audit_events audit_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: object_metadata fk_object_metadata_schema_id; Type: FK CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.object_metadata
    ADD CONSTRAINT fk_object_metadata_schema_id FOREIGN KEY (schema_id) REFERENCES public.metadata_schemas(id) ON DELETE SET NULL;


--
-- Name: object_metadata object_metadata_object_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.object_metadata
    ADD CONSTRAINT object_metadata_object_id_fkey FOREIGN KEY (object_id) REFERENCES public.objects(id) ON DELETE CASCADE;


--
-- Name: objects objects_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.objects
    ADD CONSTRAINT objects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: artesca_app
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO artesca_app;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO artesca_app;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO artesca_app;


--
-- PostgreSQL database dump complete
--

\unrestrict QvoV8hSvt362mGDIXQXdldeMW8cc15dGqbcXry1Jatyfzq3GSGXx3oRco6fQi0H

