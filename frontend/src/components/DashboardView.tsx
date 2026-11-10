import React from 'react'
import type { ObjectItem } from '../types'
import type { NavTab } from './Sidebar'
import { formatBytes } from '../utils/formatters'

interface DashboardViewProps {
  objects: ObjectItem[]
  auditCount: number
  onNavigate: (tab: NavTab) => void
  onViewObject: (id: number) => void
  onDownloadObject: (item: ObjectItem) => void
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  objects,
  auditCount,
  onNavigate,
  onViewObject,
  onDownloadObject,
}) => {
  const totalSizeBytes = objects.reduce((acc, curr) => acc + (curr.size_bytes || 0), 0)
  const uniqueBuckets = Array.from(new Set(objects.map((o) => o.bucket))).filter(Boolean)
  const recentObjects = objects.slice(0, 5)

  return (
    <div className="page-content">
      {/* Welcome Hero */}
      <div className="welcome-card">
        <div>
          <span className="eyebrow">ENTERPRISE OBJECT MANAGEMENT PLATFORM</span>
          <h2>Scality ARTESCA Storage & Metadata</h2>
          <p>
            Unified S3 object storage with visual boolean AST queries, native PostgreSQL JSONB indexing,
            enforced metadata schemas, and auditable storage compliance.
          </p>
          <div className="welcome-actions">
            <button
              type="button"
              className="primary-button"
              onClick={() => onNavigate('search')}
              id="hero-search-btn"
            >
              🔍 Object Explorer & Query
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={() => onNavigate('upload')}
              id="hero-upload-btn"
            >
              ⬆️ Upload Object
            </button>
          </div>
        </div>
        <div className="welcome-icon">⚡</div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📁</div>
          <div>
            <span>Indexed Objects</span>
            <strong>{objects.length}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💾</div>
          <div>
            <span>Total Storage Consumed</span>
            <strong>{formatBytes(totalSizeBytes)}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🪣</div>
          <div>
            <span>Active S3 Buckets</span>
            <strong>{uniqueBuckets.length || 1}</strong>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🛡️</div>
          <div>
            <span>Audit Trail Entries</span>
            <strong>{auditCount}</strong>
          </div>
        </div>
      </div>

      {/* Enterprise Capabilities Quick Links */}
      <div className="feature-grid">
        <div
          className="feature-card"
          onClick={() => onNavigate('search')}
          id="feature-card-query-builder"
        >
          <div className="feature-card-header">
            <div className="feature-card-icon">🧠</div>
            <h4>Visual Query Builder</h4>
          </div>
          <p>
            Build nested AND / OR / NOT expressions with recursive AST evaluation against PostgreSQL JSONB metadata.
          </p>
          <div className="feature-card-footer">
            <span>Explore Query Builder</span>
            <span className="arrow">→</span>
          </div>
        </div>

        <div
          className="feature-card"
          onClick={() => onNavigate('schemas')}
          id="feature-card-schemas"
        >
          <div className="feature-card-header">
            <div className="feature-card-icon">📐</div>
            <h4>Metadata Schemas</h4>
          </div>
          <p>
            Manage typed templates with data type enforcement, required attributes, and interactive sandbox validation.
          </p>
          <div className="feature-card-footer">
            <span>Configure Schemas</span>
            <span className="arrow">→</span>
          </div>
        </div>

        <div
          className="feature-card"
          onClick={() => onNavigate('search')}
          id="feature-card-jsonb"
        >
          <div className="feature-card-header">
            <div className="feature-card-icon">⚡</div>
            <h4>PostgreSQL JSONB Indexing</h4>
          </div>
          <p>
            High-performance GIN index acceleration for flexible custom attributes, key existence, and numeric ranges.
          </p>
          <div className="feature-card-footer">
            <span>Search JSONB Catalog</span>
            <span className="arrow">→</span>
          </div>
        </div>
      </div>

      {/* Recent Objects Section */}
      <div className="section-card">
        <div className="section-header">
          <div>
            <h3>Recent Objects</h3>
            <p>Latest files stored and indexed in ARTESCA S3 storage</p>
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={() => onNavigate('search')}
          >
            View All ({objects.length})
          </button>
        </div>

        {recentObjects.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📂</div>
            <h3>No objects stored yet</h3>
            <p>Upload your first document or file to start managing metadata.</p>
            <button
              type="button"
              className="primary-button"
              style={{ marginTop: '14px' }}
              onClick={() => onNavigate('upload')}
            >
              Upload File
            </button>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>File Name</th>
                  <th>Bucket</th>
                  <th>Size</th>
                  <th>Classification</th>
                  <th>Department / Project</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentObjects.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
                        #{item.id}
                      </span>
                    </td>
                    <td>
                      <div className="object-name">
                        <div className="file-icon">
                          {(item.filename.split('.').pop() || 'FILE').toUpperCase().slice(0, 4)}
                        </div>
                        <div>
                          <strong>{item.filename}</strong>
                          <span title={item.object_key}>{item.object_key}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="bucket-name">{item.bucket}</span>
                    </td>
                    <td>{formatBytes(item.size_bytes)}</td>
                    <td>
                      {item.metadata?.classification ? (
                        <span className="status-badge active" style={{ fontSize: '11px' }}>
                          {item.metadata.classification}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>-</span>
                      )}
                    </td>
                    <td>
                      <div className="metadata-summary">
                        {item.metadata?.department && (
                          <span>{item.metadata.department}</span>
                        )}
                        {item.metadata?.project && (
                          <span>{item.metadata.project}</span>
                        )}
                        {!item.metadata?.department && !item.metadata?.project && (
                          <span className="muted">-</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span
                        className={`status-badge ${
                          item.status.toUpperCase() === 'ACTIVE' ? 'active' : 'inactive'
                        }`}
                      >
                        <span />
                        {item.status}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          type="button"
                          className="icon-button"
                          onClick={() => onViewObject(item.id)}
                          title="View Object Details"
                        >
                          👁️ View
                        </button>
                        <button
                          type="button"
                          className="icon-button"
                          onClick={() => onDownloadObject(item)}
                          title="Download File"
                        >
                          ⬇️ Get
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
