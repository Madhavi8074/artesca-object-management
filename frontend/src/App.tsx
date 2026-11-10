import { useState, useEffect, useCallback } from 'react'
import './App.css'
import type { AuditEvent, ObjectItem, SearchFilters, UserProfile, QueryGroup } from './types'
import { ApiClient } from './services/api'
import { Sidebar, type NavTab } from './components/Sidebar'
import { Topbar } from './components/Topbar'
import { DashboardView } from './components/DashboardView'
import { SearchObjectsView } from './components/SearchObjectsView'
import { UploadObjectView } from './components/UploadObjectView'
import { AuditLogView } from './components/AuditLogView'
import { SchemaAdminView } from './components/SchemaAdminView'
import { ObjectDetailModal } from './components/ObjectDetailModal'
import { DeleteConfirmModal } from './components/DeleteConfirmModal'
import { LoginPage } from './components/LoginPage'
import { ShareModal } from './components/ShareModal'
import { NewFolderModal } from './components/NewFolderModal'

const defaultFilters: SearchFilters = {
  filename: '',
  object_key: '',
  object_key_regex: '',
  content_type: '',
  bucket: '',
  size_operator: 'none',
  size_value: '',
  classification: '',
  department: '',
  project: '',
  document_type: '',
  author: '',
  description: '',
  custom_key: '',
  custom_value: '',
}

export function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem('artesca_token') || '')
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)

  const [activeTab, setActiveTab] = useState<NavTab>('dashboard')
  const [dbConnected, setDbConnected] = useState(true)

  // Data states
  const [objects, setObjects] = useState<ObjectItem[]>([])
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [loadingObjects, setLoadingObjects] = useState(false)
  const [filters, setFilters] = useState<SearchFilters>(defaultFilters)
  const [currentPrefix, setCurrentPrefix] = useState<string>('')

  // Active visual query group
  const [activeVisualGroup, setActiveVisualGroup] = useState<QueryGroup | null>(null)

  // Notification banners
  const [successBanner, setSuccessBanner] = useState<string | null>(null)
  const [errorBanner, setErrorBanner] = useState<string | null>(null)

  // Modals
  const [selectedObjectId, setSelectedObjectId] = useState<number | null>(null)
  const [selectedObject, setSelectedObject] = useState<ObjectItem | null>(null)
  const [objectToDelete, setObjectToDelete] = useState<ObjectItem | null>(null)
  const [objectToShare, setObjectToShare] = useState<ObjectItem | null>(null)
  const [showFolderModal, setShowFolderModal] = useState(false)

  const showNotification = (message: string, isError = false) => {
    if (isError) {
      setErrorBanner(message)
      setTimeout(() => setErrorBanner(null), 6000)
    } else {
      setSuccessBanner(message)
      setTimeout(() => setSuccessBanner(null), 5000)
    }
  }

  // Handle unauthorized event
  useEffect(() => {
    const handleUnauthorized = () => {
      setToken('')
      setUserProfile(null)
      setObjects([])
      setAuditEvents([])
      showNotification('Session expired. Please log in again.', true)
    }
    window.addEventListener('artesca:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('artesca:unauthorized', handleUnauthorized)
  }, [])

  // Check DB health
  const checkHealth = useCallback(async () => {
    try {
      const res = await ApiClient.getDatabaseHealth()
      setDbConnected(res.database === 'connected')
    } catch {
      setDbConnected(false)
    }
  }, [])

  // Load user profile
  const loadProfile = useCallback(async () => {
    try {
      const profile = await ApiClient.getMe()
      setUserProfile(profile)
    } catch {
      // Token might be invalid
    }
  }, [])

  // Fetch objects (handles standard filters, prefix navigation, or active visual AST query)
  const fetchObjects = useCallback(
    async (
      visualGroup = activeVisualGroup,
      currentFilters = filters,
      prefix = currentPrefix,
    ) => {
      setLoadingObjects(true)
      try {
        let result: ObjectItem[]
        if (visualGroup) {
          result = await ApiClient.queryObjects({
            root: visualGroup,
          })
        } else {
          const effectiveFilters = {
            ...currentFilters,
            object_key: prefix ? prefix : currentFilters.object_key,
          }
          result = await ApiClient.searchObjects(effectiveFilters)
        }
        setObjects(result)
      } catch (err) {
        showNotification(err instanceof Error ? err.message : 'Failed to retrieve objects', true)
      } finally {
        setLoadingObjects(false)
      }
    },
    [activeVisualGroup, filters, currentPrefix],
  )

  // Load audit logs
  const fetchAuditLogs = useCallback(async () => {
    try {
      const res = await ApiClient.listAuditEvents()
      setAuditEvents(res)
    } catch {
      // Permission restriction
    }
  }, [])

  // Initial load on authentication
  useEffect(() => {
    if (token) {
      checkHealth()
      loadProfile()
      fetchObjects(null, defaultFilters, '')
      fetchAuditLogs()
    }
  }, [token])

  // Fetch full details of object when selected
  useEffect(() => {
    if (selectedObjectId) {
      ApiClient.getObject(selectedObjectId)
        .then((res) => setSelectedObject(res))
        .catch((err) => {
          showNotification(err instanceof Error ? err.message : 'Failed to load object details', true)
          setSelectedObjectId(null)
        })
    } else {
      setSelectedObject(null)
    }
  }, [selectedObjectId])

  // Auth actions
  const handleLogin = async (u: string, p: string) => {
    setAuthLoading(true)
    setAuthError(null)
    try {
      const res = await ApiClient.login(u, p)
      setToken(res.access_token)
      showNotification(`Welcome back, ${res.username}!`)
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : 'Invalid credentials')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleRegister = async (
    u: string,
    p: string,
    email?: string,
    displayName?: string,
    department?: string,
  ) => {
    setAuthLoading(true)
    setAuthError(null)
    try {
      const res = await ApiClient.register(u, p, email, displayName, department)
      setToken(res.access_token)
      showNotification(`Account created successfully! Welcome, ${res.username}!`)
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogout = () => {
    ApiClient.clearAuth()
    setToken('')
    setUserProfile(null)
    setObjects([])
    setAuditEvents([])
    showNotification('Signed out successfully.')
  }

  // Filter & Folder actions
  const handleFilterChange = <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  const handleSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setActiveVisualGroup(null)
    fetchObjects(null, filters, currentPrefix)
  }

  const handleClearFilters = () => {
    setFilters(defaultFilters)
    setActiveVisualGroup(null)
    setCurrentPrefix('')
    fetchObjects(null, defaultFilters, '')
  }

  const handleVisualQuery = (group: QueryGroup) => {
    setActiveVisualGroup(group)
    fetchObjects(group, filters, currentPrefix)
  }

  const handleSelectPrefix = (prefix: string) => {
    setCurrentPrefix(prefix)
    fetchObjects(activeVisualGroup, filters, prefix)
  }

  // Folder creation
  const handleCreateFolder = async (folderName: string) => {
    try {
      const res = await ApiClient.createFolder(folderName, currentPrefix)
      showNotification(`Folder "${res.filename}" created successfully!`)
      fetchObjects(activeVisualGroup, filters, currentPrefix)
      fetchAuditLogs()
    } catch (err) {
      showNotification(err instanceof Error ? err.message : 'Failed to create folder', true)
      throw err
    }
  }

  // Upload action
  const handleUpload = async (formData: FormData) => {
    try {
      const res = await ApiClient.uploadObject(formData)
      showNotification(`Object "${res.filename}" uploaded successfully! (ID: #${res.id})`)
      fetchObjects(null, defaultFilters, currentPrefix)
      fetchAuditLogs()
      setActiveTab('search')
    } catch (err) {
      showNotification(err instanceof Error ? err.message : 'Upload failed', true)
      throw err
    }
  }

  // Save metadata
  const handleSaveMetadata = async (id: number, payload: Record<string, unknown>) => {
    try {
      await ApiClient.updateObject(id, payload)
      showNotification('Metadata attributes saved successfully.')
      fetchObjects(activeVisualGroup, filters, currentPrefix)
      fetchAuditLogs()
      setSelectedObjectId(null)
    } catch (err) {
      showNotification(err instanceof Error ? err.message : 'Update failed', true)
      throw err
    }
  }

  // Delete object
  const handleDeleteObject = async (id: number) => {
    try {
      await ApiClient.deleteObject(id)
      showNotification('Item and catalog metadata deleted successfully.')
      setObjects((prev) => prev.filter((o) => o.id !== id))
      fetchAuditLogs()
      setObjectToDelete(null)
    } catch (err) {
      showNotification(err instanceof Error ? err.message : 'Delete failed', true)
      throw err
    }
  }

  // Download action
  const handleDownload = async (item: ObjectItem) => {
    try {
      await ApiClient.downloadObject(item.id, item.filename)
      showNotification(`Downloaded "${item.filename}"`)
      fetchAuditLogs()
    } catch (err) {
      showNotification(err instanceof Error ? err.message : 'Download failed', true)
    }
  }

  if (!token) {
    return (
      <LoginPage
        onLogin={handleLogin}
        onRegister={handleRegister}
        loading={authLoading}
        error={authError}
      />
    )
  }

  const pageTitles: Record<NavTab, { title: string; subtitle: string }> = {
    dashboard: {
      title: 'EasyStore Dashboard',
      subtitle: 'S3-compatible object storage health and catalog statistics (Scality ARTESCA / MinIO)',
    },
    search: {
      title: 'Objects Catalog & Query Engine',
      subtitle: 'Hierarchical folder navigation, visual boolean AST queries, and JSONB indexing',
    },
    upload: {
      title: 'Object Ingestion',
      subtitle: 'Stream files to S3 with metadata schema enforcement and JSONB attribute indexing',
    },
    schemas: {
      title: 'Metadata Schema Administration',
      subtitle: 'Define, enforce, and validate custom metadata models with field types',
    },
    audit: {
      title: 'Security & Operations Audit Trail',
      subtitle: 'Immutable compliance log and activity telemetry recorded in PostgreSQL',
    },
  }

  return (
    <div className="app-shell">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        userProfile={userProfile}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <div className="main-content">
        <Topbar
          title={pageTitles[activeTab]?.title || 'EasyStore Object Management'}
          subtitle={pageTitles[activeTab]?.subtitle || ''}
          userProfile={userProfile}
          dbConnected={dbConnected}
        />

        {/* Global Notifications */}
        {successBanner && (
          <div className="success-banner">
            <span>✓</span>
            <div>{successBanner}</div>
            <button type="button" onClick={() => setSuccessBanner(null)}>
              ×
            </button>
          </div>
        )}

        {errorBanner && (
          <div className="error-banner">
            <span>⚠️</span>
            <div>{errorBanner}</div>
            <button type="button" onClick={() => setErrorBanner(null)}>
              ×
            </button>
          </div>
        )}

        {/* Views */}
        {activeTab === 'dashboard' && (
          <DashboardView
            objects={objects}
            auditCount={objects.length || auditEvents.length}
            onNavigate={setActiveTab}
            onViewObject={(id) => setSelectedObjectId(id)}
            onDownloadObject={handleDownload}
          />
        )}

        {activeTab === 'search' && (
          <SearchObjectsView
            objects={objects}
            loading={loadingObjects}
            filters={filters}
            currentPrefix={currentPrefix}
            onFilterChange={handleFilterChange}
            onSearch={handleSearch}
            onClearFilters={handleClearFilters}
            onVisualQuery={handleVisualQuery}
            onViewObject={(id) => setSelectedObjectId(id)}
            onDownloadObject={handleDownload}
            onShareObject={(item) => setObjectToShare(item)}
            onRequestDelete={(item) => setObjectToDelete(item)}
            onNavigateUpload={() => setActiveTab('upload')}
            onCreateFolder={() => setShowFolderModal(true)}
            onSelectPrefix={handleSelectPrefix}
            onReload={() => fetchObjects(activeVisualGroup, filters, currentPrefix)}
            userProfile={userProfile}
          />
        )}

        {activeTab === 'upload' && (
          <UploadObjectView
            onUpload={handleUpload}
            loading={loadingObjects}
            onSuccess={() => {
              fetchObjects(null, defaultFilters, currentPrefix)
              fetchAuditLogs()
            }}
          />
        )}

        {activeTab === 'schemas' && <SchemaAdminView userProfile={userProfile} />}
        {activeTab === 'audit' && <AuditLogView onRefresh={fetchAuditLogs} />}
      </div>

      {/* Object Details & Metadata Modal */}
      {selectedObject && (
        <ObjectDetailModal
          objectItem={selectedObject}
          onClose={() => setSelectedObjectId(null)}
          onSaveMetadata={handleSaveMetadata}
          onDownload={handleDownload}
          userProfile={userProfile}
        />
      )}

      {/* Delete Confirmation Modal */}
      {objectToDelete && (
        <DeleteConfirmModal
          objectItem={objectToDelete}
          onClose={() => setObjectToDelete(null)}
          onConfirm={handleDeleteObject}
        />
      )}

      {/* Presigned Share Link Modal */}
      {objectToShare && (
        <ShareModal
          objectItem={objectToShare}
          onClose={() => setObjectToShare(null)}
        />
      )}

      {/* New Folder Modal */}
      {showFolderModal && (
        <NewFolderModal
          currentPrefix={currentPrefix}
          onClose={() => setShowFolderModal(false)}
          onCreate={handleCreateFolder}
        />
      )}
    </div>
  )
}

export default App
