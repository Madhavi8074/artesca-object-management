export interface Metadata {
  classification: string | null
  department: string | null
  project: string | null
  document_type: string | null
  author: string | null
  description: string | null
  schema_id?: number | null
  custom_metadata: Record<string, unknown> | null
}

export interface ObjectItem {
  id: number
  bucket: string
  object_key: string
  filename: string
  content_type: string | null
  size_bytes: number
  etag?: string | null
  version_id?: string | null
  owner_id?: number | null
  status: string
  is_folder?: boolean
  metadata?: Metadata | null
  created_at?: string
  updated_at?: string
}

export interface ShareLinkResponse {
  object_id: number
  filename: string
  share_url: string
  expires_in: number
  created_at: string
}

export interface AuditEvent {
  id: number
  action: string
  object_id: number | null
  user_id: number | null
  username: string | null
  resource_type: string | null
  resource_id: string | null
  success: boolean
  error_code: string | null
  details: Record<string, unknown> | null
  timestamp: string
}

export interface UserProfile {
  id: number
  username: string
  display_name: string | null
  email: string | null
  department: string | null
  roles: string[]
  permissions: string[]
}

export interface SearchFilters {
  filename: string
  object_key: string
  object_key_regex: string
  content_type: string
  bucket: string
  prefix?: string
  size_operator: 'none' | 'greater' | 'less' | 'equal'
  size_value: string
  classification: string
  department: string
  project: string
  document_type: string
  author: string
  description: string
  custom_key: string
  custom_value: string
}

// -------------------------------------------------------------
// METADATA SCHEMAS
// -------------------------------------------------------------
export interface SchemaField {
  name: string
  label: string
  type: 'string' | 'number' | 'boolean' | 'date' | 'enum'
  required: boolean
  description?: string
  options?: string[]
  default?: unknown
}

export interface MetadataSchema {
  id: number
  name: string
  description?: string | null
  version: number | string
  is_active: boolean
  fields: SchemaField[]
  created_at?: string
  updated_at?: string
}

// -------------------------------------------------------------
// VISUAL QUERY BUILDER (AST)
// -------------------------------------------------------------
export interface QueryRule {
  field: string
  operator: string
  value: unknown
}

export interface QueryGroup {
  combinator: 'AND' | 'OR' | 'NOT'
  rules: (QueryRule | QueryGroup)[]
}

export interface AdvancedQueryRequest {
  root: QueryGroup
}
