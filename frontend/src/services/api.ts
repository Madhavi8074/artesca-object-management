import type {
  AuditEvent,
  MetadataSchema,
  ObjectItem,
  SearchFilters,
  UserProfile,
  AdvancedQueryRequest,
  ShareLinkResponse,
} from '../types'

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== 'undefined'
    ? `http://${window.location.hostname}:8000`
    : 'http://127.0.0.1:8000')

export class ApiClient {
  private static getToken(): string {
    return localStorage.getItem('artesca_token') || ''
  }

  public static setAuth(token: string, username: string): void {
    localStorage.setItem('artesca_token', token)
    localStorage.setItem('artesca_username', username)
  }

  public static clearAuth(): void {
    localStorage.removeItem('artesca_token')
    localStorage.removeItem('artesca_username')
  }

  public static getSavedUsername(): string {
    return localStorage.getItem('artesca_username') || ''
  }

  private static async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`
    const headers = new Headers(options.headers || {})

    const token = this.getToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (response.status === 401) {
      this.clearAuth()
      window.dispatchEvent(new CustomEvent('artesca:unauthorized'))
      throw new Error('Session expired or authentication invalid. Please sign in again.')
    }

    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`
      try {
        const errorJson = await response.json()
        errorMessage = errorJson.detail || errorJson.message || errorMessage
      } catch {
        // use default error message
      }
      throw new Error(errorMessage)
    }

    if (response.status === 204) {
      return {} as T
    }

    return response.json()
  }

  // -------------------------------------------------------------
  // AUTH
  // -------------------------------------------------------------

  public static async login(
    username: string,
    password: string,
  ): Promise<{ access_token: string; username: string; user_id: number }> {
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    })

    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed')
    }

    this.setAuth(data.access_token, data.username)
    return data
  }

  public static async register(
    username: string,
    password: string,
    email?: string,
    displayName?: string,
    department?: string,
  ): Promise<{ access_token: string; username: string; user_id: number }> {
    const response = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        password,
        email: email || undefined,
        display_name: displayName || undefined,
        department: department || undefined,
      }),
    })

    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || 'Registration failed')
    }

    this.setAuth(data.access_token, data.username)
    return data
  }

  public static async getMe(): Promise<UserProfile> {
    return this.request<UserProfile>('/api/v1/auth/me')
  }

  // -------------------------------------------------------------
  // HEALTH
  // -------------------------------------------------------------

  public static async getHealth(): Promise<{ status: string; service: string }> {
    const res = await fetch(`${API_BASE}/health`)
    return res.json()
  }

  public static async getDatabaseHealth(): Promise<{ database: string; test: number }> {
    const res = await fetch(`${API_BASE}/health/database`)
    return res.json()
  }

  public static async getStorageHealth(): Promise<Record<string, unknown>> {
    const res = await fetch(`${API_BASE}/health/storage`)
    return res.json()
  }

  // -------------------------------------------------------------
  // OBJECTS & FOLDERS
  // -------------------------------------------------------------

  public static async listObjects(bucket?: string, prefix?: string): Promise<ObjectItem[]> {
    const params = new URLSearchParams()
    if (bucket) params.set('bucket', bucket)
    if (prefix) params.set('prefix', prefix)
    const query = params.toString()
    return this.request<ObjectItem[]>(`/api/v1/objects/${query ? `?${query}` : ''}`)
  }

  public static async listBuckets(): Promise<Array<{ name: string; created_at?: string }>> {
    return this.request<Array<{ name: string; created_at?: string }>>('/api/v1/objects/buckets')
  }

  public static async createFolder(
    folderName: string,
    parentPrefix?: string,
    bucket?: string,
  ): Promise<ObjectItem & { message: string }> {
    return this.request<ObjectItem & { message: string }>('/api/v1/objects/folders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        folder_name: folderName,
        parent_prefix: parentPrefix || '',
        bucket: bucket || undefined,
      }),
    })
  }

  public static async getObject(id: number): Promise<ObjectItem> {
    return this.request<ObjectItem>(`/api/v1/objects/${id}`)
  }

  public static async getShareLink(objectId: number, expiresIn: number = 3600): Promise<ShareLinkResponse> {
    return this.request<ShareLinkResponse>(`/api/v1/objects/${objectId}/share?expires_in=${expiresIn}`)
  }

  public static async getPresignedDownloadUrl(objectId: number, expiresIn: number = 3600): Promise<{ download_url: string }> {
    return this.request<{ download_url: string }>(`/api/v1/objects/${objectId}/presigned-download?expires_in=${expiresIn}`)
  }

  public static async queryObjects(payload: AdvancedQueryRequest): Promise<ObjectItem[]> {
    return this.request<ObjectItem[]>('/api/v1/search/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  }

  public static async searchObjects(filters: Partial<SearchFilters>): Promise<ObjectItem[]> {
    const params = new URLSearchParams()

    if (filters.filename?.trim()) params.set('filename', filters.filename.trim())
    if (filters.object_key?.trim()) params.set('object_key', filters.object_key.trim())
    if (filters.object_key_regex?.trim()) params.set('object_key_regex', filters.object_key_regex.trim())
    if (filters.content_type?.trim()) params.set('content_type', filters.content_type.trim())
    if (filters.bucket?.trim()) params.set('bucket', filters.bucket.trim())

    if (filters.size_value?.trim()) {
      const num = Number(filters.size_value)
      if (!Number.isNaN(num)) {
        if (filters.size_operator === 'greater') params.set('size_gt', String(num))
        if (filters.size_operator === 'less') params.set('size_lt', String(num))
        if (filters.size_operator === 'equal') {
          params.set('min_size', String(num))
          params.set('max_size', String(num))
        }
      }
    }

    if (filters.classification?.trim()) params.set('classification', filters.classification.trim())
    if (filters.department?.trim()) params.set('department', filters.department.trim())
    if (filters.project?.trim()) params.set('project', filters.project.trim())
    if (filters.document_type?.trim()) params.set('document_type', filters.document_type.trim())
    if (filters.author?.trim()) params.set('author', filters.author.trim())
    if (filters.description?.trim()) params.set('description', filters.description.trim())
    if (filters.custom_key?.trim()) params.set('custom_key', filters.custom_key.trim())
    if (filters.custom_value?.trim()) params.set('custom_value', filters.custom_value.trim())

    const query = params.toString()
    return this.request<ObjectItem[]>(`/api/v1/search/objects${query ? `?${query}` : ''}`)
  }

  public static async uploadObject(formData: FormData): Promise<ObjectItem & { message: string }> {
    return this.request<ObjectItem & { message: string }>('/api/v1/objects/upload', {
      method: 'POST',
      body: formData,
    })
  }

  public static async updateObject(
    id: number,
    payload: Record<string, unknown>,
  ): Promise<ObjectItem & { message: string }> {
    return this.request<ObjectItem & { message: string }>(`/api/v1/objects/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
  }

  public static async deleteObject(id: number): Promise<{ id: number; message: string }> {
    return this.request<{ id: number; message: string }>(`/api/v1/objects/${id}`, {
      method: 'DELETE',
    })
  }

  public static async downloadObject(id: number, fallbackFilename: string): Promise<void> {
    const url = `${API_BASE}/api/v1/objects/${id}/download`
    const token = this.getToken()
    const headers = new Headers()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }

    const response = await fetch(url, { headers })
    if (!response.ok) {
      let detail = 'Download failed'
      try {
        const errorJson = await response.json()
        detail = errorJson.detail || detail
      } catch {
        // ignore
      }
      throw new Error(detail)
    }

    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = fallbackFilename
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(downloadUrl)
  }

  // -------------------------------------------------------------
  // METADATA SCHEMAS
  // -------------------------------------------------------------

  public static async listSchemas(): Promise<MetadataSchema[]> {
    return this.request<MetadataSchema[]>('/api/v1/schemas/')
  }

  public static async getSchema(id: number): Promise<MetadataSchema> {
    return this.request<MetadataSchema>(`/api/v1/schemas/${id}`)
  }

  public static async createSchema(payload: {
    name: string
    description?: string
    is_active?: boolean
    fields: Array<{
      name: string
      label: string
      type: string
      required: boolean
      description?: string
      options?: string[]
      default?: unknown
    }>
  }): Promise<MetadataSchema> {
    return this.request<MetadataSchema>('/api/v1/schemas/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  }

  public static async updateSchema(
    id: number,
    payload: {
      name?: string
      description?: string
      is_active?: boolean
      fields?: Array<{
        name: string
        label: string
        type: string
        required: boolean
        description?: string
        options?: string[]
        default?: unknown
      }>
    },
  ): Promise<MetadataSchema> {
    return this.request<MetadataSchema>(`/api/v1/schemas/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  }

  public static async deleteSchema(id: number): Promise<void> {
    await this.request(`/api/v1/schemas/${id}`, {
      method: 'DELETE',
    })
  }

  public static async validateSchema(
    schemaId: number,
    metadata: Record<string, unknown>,
  ): Promise<{ schema_id: number; schema_name: string; is_valid: boolean; errors: string[] }> {
    return this.request(`/api/v1/schemas/${schemaId}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ metadata }),
    })
  }

  // -------------------------------------------------------------
  // AUDIT
  // -------------------------------------------------------------

  public static async listAuditEvents(params: {
    action?: string
    user_id?: number
    username?: string
    object_id?: number
    resource_type?: string
    success?: boolean
    start_date?: string
    end_date?: string
  } = {}): Promise<AuditEvent[]> {
    const searchParams = new URLSearchParams()
    if (params.action) searchParams.set('action', params.action)
    if (params.user_id) searchParams.set('user_id', String(params.user_id))
    if (params.username) searchParams.set('username', params.username)
    if (params.object_id) searchParams.set('object_id', String(params.object_id))
    if (params.resource_type) searchParams.set('resource_type', params.resource_type)
    if (params.success !== undefined) searchParams.set('success', String(params.success))
    if (params.start_date) searchParams.set('start_date', params.start_date)
    if (params.end_date) searchParams.set('end_date', params.end_date)

    const query = searchParams.toString()
    return this.request<AuditEvent[]>(`/api/v1/audit/${query ? `?${query}` : ''}`)
  }

  public static async listObjectAuditEvents(objectId: number): Promise<AuditEvent[]> {
    return this.request<AuditEvent[]>(`/api/v1/audit/object/${objectId}`)
  }
}
