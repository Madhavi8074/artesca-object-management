import React, { useState, useEffect } from 'react'
import type { AuditEvent, ObjectItem, UserProfile } from '../types'
import { formatBytes, formatDate } from '../utils/formatters'
import { ApiClient } from '../services/api'

interface ObjectDetailModalProps {
  objectItem: ObjectItem | null
  onClose: () => void
  onSaveMetadata: (id: number, payload: Record<string, unknown>) => Promise<void>
  onDownload: (item: ObjectItem) => void
  userProfile: UserProfile | null
}

export const ObjectDetailModal: React.FC<ObjectDetailModalProps> = ({
  objectItem,
  onClose,
  onSaveMetadata,
  onDownload,
  userProfile,
}) => {
  const [activeTab, setActiveTab] = useState<'metadata' | 'audit'>('metadata')
  const [classification, setClassification] = useState('')
  const [department, setDepartment] = useState('')
  const [project, setProject] = useState('')
  const [documentType, setDocumentType] = useState('')
  const [author, setAuthor] = useState('')
  const [description, setDescription] = useState('')
  const [customMetadata, setCustomMetadata] = useState('{}')
  const [jsonError, setJsonError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [loadingAudit, setLoadingAudit] = useState(false)

  const canEdit =
    userProfile?.permissions.includes('OBJECT_UPDATE') ||
    userProfile?.roles.includes('ADMIN') ||
    userProfile?.roles.includes('EDITOR') ||
    false

  useEffect(() => {
    if (objectItem) {
      setClassification(objectItem.metadata?.classification || '')
      setDepartment(objectItem.metadata?.department || '')
      setProject(objectItem.metadata?.project || '')
      setDocumentType(objectItem.metadata?.document_type || '')
      setAuthor(objectItem.metadata?.author || '')
      setDescription(objectItem.metadata?.description || '')
      setCustomMetadata(
        JSON.stringify(objectItem.metadata?.custom_metadata || {}, null, 2),
      )
      setJsonError(null)

      // Fetch audit history for this specific object
      setLoadingAudit(true)
      ApiClient.listObjectAuditEvents(objectItem.id)
        .then((res) => setAuditEvents(res))
        .catch(() => setAuditEvents([]))
        .finally(() => setLoadingAudit(false))
    }
  }, [objectItem])

  if (!objectItem) return null

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setJsonError(null)

    let parsedCustom: Record<string, unknown> = {}
    if (customMetadata.trim()) {
      try {
        parsedCustom = JSON.parse(customMetadata)
        if (typeof parsedCustom !== 'object' || Array.isArray(parsedCustom)) {
          setJsonError('Custom metadata must be a JSON object.')
          return
        }
      } catch (err) {
        setJsonError(`Invalid JSON: ${err instanceof Error ? err.message : String(err)}`)
        return
      }
    }

    setSaving(true)
    try {
      await onSaveMetadata(objectItem.id, {
        classification: classification || null,
        department: department || null,
        project: project || null,
        document_type: documentType || null,
        author: author || null,
        description: description || null,
        custom_metadata: parsedCustom,
      })
      onClose()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>Object #{objectItem.id} Details</h2>
            <p style={{ margin: '3px 0 0', color: 'var(--text-secondary)', fontSize: '12px' }}>
              {objectItem.filename}
            </p>
          </div>
          <button type="button" className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          {/* Storage Information Grid */}
          <div className="detail-grid">
            <div className="detail-item">
              <span>File Name</span>
              <strong>{objectItem.filename}</strong>
            </div>

            <div className="detail-item">
              <span>Target S3 Bucket</span>
              <strong>{objectItem.bucket}</strong>
            </div>

            <div className="detail-item">
              <span>Object Key</span>
              <strong style={{ wordBreak: 'break-all' }}>{objectItem.object_key}</strong>
            </div>

            <div className="detail-item">
              <span>Content Type</span>
              <strong>{objectItem.content_type || 'application/octet-stream'}</strong>
            </div>

            <div className="detail-item">
              <span>File Size</span>
              <strong>{formatBytes(objectItem.size_bytes)}</strong>
            </div>

            <div className="detail-item">
              <span>Status</span>
              <strong style={{ color: 'var(--success)' }}>{objectItem.status}</strong>
            </div>
          </div>

          {/* Tab Selector */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '22px', borderBottom: '1px solid var(--border)' }}>
            <button
              type="button"
              className="text-button"
              style={{
                padding: '8px 12px',
                borderBottom: activeTab === 'metadata' ? '2px solid var(--primary)' : 'none',
                color: activeTab === 'metadata' ? 'var(--primary)' : 'var(--text-secondary)',
              }}
              onClick={() => setActiveTab('metadata')}
            >
              Metadata Catalog
            </button>
            <button
              type="button"
              className="text-button"
              style={{
                padding: '8px 12px',
                borderBottom: activeTab === 'audit' ? '2px solid var(--primary)' : 'none',
                color: activeTab === 'audit' ? 'var(--primary)' : 'var(--text-secondary)',
              }}
              onClick={() => setActiveTab('audit')}
            >
              Audit History ({auditEvents.length})
            </button>
          </div>

          {/* Tab 1: Edit Metadata */}
          {activeTab === 'metadata' && (
            <form onSubmit={handleSave} style={{ marginTop: '16px' }}>
              <div className="form-grid" style={{ padding: 0 }}>
                <label>
                  Classification
                  <select
                    disabled={!canEdit}
                    value={classification}
                    onChange={(e) => setClassification(e.target.value)}
                  >
                    <option value="">None</option>
                    <option value="PUBLIC">PUBLIC</option>
                    <option value="INTERNAL">INTERNAL</option>
                    <option value="CONFIDENTIAL">CONFIDENTIAL</option>
                    <option value="RESTRICTED">RESTRICTED</option>
                  </select>
                </label>

                <label>
                  Department
                  <input
                    type="text"
                    disabled={!canEdit}
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                  />
                </label>

                <label>
                  Project
                  <input
                    type="text"
                    disabled={!canEdit}
                    value={project}
                    onChange={(e) => setProject(e.target.value)}
                  />
                </label>

                <label>
                  Document Type
                  <input
                    type="text"
                    disabled={!canEdit}
                    value={documentType}
                    onChange={(e) => setDocumentType(e.target.value)}
                  />
                </label>

                <label>
                  Author
                  <input
                    type="text"
                    disabled={!canEdit}
                    value={author}
                    onChange={(e) => setAuthor(e.target.value)}
                  />
                </label>

                <label>
                  Description
                  <input
                    type="text"
                    disabled={!canEdit}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </label>

                <label className="full-width">
                  Custom JSON Attributes
                  <textarea
                    rows={6}
                    disabled={!canEdit}
                    value={customMetadata}
                    onChange={(e) => {
                      setCustomMetadata(e.target.value)
                      setJsonError(null)
                    }}
                    style={{
                      fontFamily: 'monospace',
                      fontSize: '12px',
                      borderColor: jsonError ? 'var(--danger)' : undefined,
                    }}
                  />
                  {jsonError && (
                    <span style={{ color: 'var(--danger)', fontSize: '11px', marginTop: '4px' }}>
                      {jsonError}
                    </span>
                  )}
                </label>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => onDownload(objectItem)}
                  id="modal-download-btn"
                >
                  ⬇️ Download File
                </button>
                {canEdit && (
                  <button
                    type="submit"
                    className="primary-button"
                    disabled={saving}
                    id="modal-save-btn"
                  >
                    {saving ? 'Saving Changes...' : '💾 Save Metadata'}
                  </button>
                )}
              </div>
            </form>
          )}

          {/* Tab 2: Object Audit Log */}
          {activeTab === 'audit' && (
            <div style={{ marginTop: '16px' }}>
              {loadingAudit ? (
                <div className="loading-state">
                  <div className="spinner" />
                  <span>Loading audit trail...</span>
                </div>
              ) : auditEvents.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)', padding: '20px 0' }}>
                  No audit entries recorded for this object.
                </p>
              ) : (
                <div className="audit-list" style={{ padding: 0 }}>
                  {auditEvents.map((evt) => (
                    <div key={evt.id} className="audit-item" style={{ padding: '12px 0' }}>
                      <div className={`audit-icon ${evt.success ? 'success' : 'failure'}`}>
                        {evt.success ? '✓' : '✗'}
                      </div>
                      <div className="audit-content">
                        <div className="audit-top">
                          <strong>{evt.action}</strong>
                          <span>{formatDate(evt.timestamp)}</span>
                        </div>
                        <p style={{ margin: '4px 0', fontSize: '11px' }}>
                          Actor: @{evt.username || 'System'}
                        </p>
                        {evt.details && Object.keys(evt.details).length > 0 && (
                          <pre style={{ margin: '4px 0', padding: '8px', fontSize: '10px' }}>
                            {JSON.stringify(evt.details, null, 2)}
                          </pre>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
