import React, { useState, useEffect } from 'react'
import type { AuditEvent } from '../types'
import { formatDate } from '../utils/formatters'
import { ApiClient } from '../services/api'

interface AuditLogViewProps {
  onRefresh?: () => void
}

export const AuditLogView: React.FC<AuditLogViewProps> = () => {
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [actionFilter, setActionFilter] = useState('')
  const [usernameFilter, setUsernameFilter] = useState('')

  const loadEvents = async () => {
    try {
      setLoading(true)
      setError(null)

      const data = await ApiClient.listAuditEvents({
        action: actionFilter || undefined,
        username: usernameFilter.trim() || undefined,
      })
      setEvents(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadEvents()
  }, [actionFilter])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    loadEvents()
  }

  const handleClearFilters = () => {
    setActionFilter('')
    setUsernameFilter('')
  }

  const getActionBadgeClass = (action: string, success: boolean) => {
    if (!success) return 'badge-danger'
    if (action.includes('DELETE')) return 'badge-danger'
    if (action.includes('UPLOAD')) return 'badge-success'
    if (action.includes('LOGIN')) return 'badge-info'
    if (action.includes('SCHEMA')) return 'badge-primary'
    return 'badge-secondary'
  }

  return (
    <div className="page-content">
      {/* Header */}
      <div className="page-actions">
        <div>
          <h2>Audit Trail & Compliance Log</h2>
          <p>Immutable audit trail tracking user operations, storage actions, and metadata changes.</p>
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={loadEvents}
          title="Refresh Logs"
          id="refresh-audit-btn"
        >
          🔄 Refresh Log
        </button>
      </div>

      {error && <div className="alert alert-danger mb-4">{error}</div>}

      {/* Filter Card */}
      <form onSubmit={handleSearchSubmit} className="filter-card mb-4">
        <div className="search-wrapper">
          <span>🔍</span>
          <input
            type="text"
            placeholder="Filter by username..."
            value={usernameFilter}
            onChange={(e) => setUsernameFilter(e.target.value)}
          />
        </div>

        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
        >
          <option value="">All Actions</option>
          <option value="OBJECT_UPLOAD">OBJECT_UPLOAD</option>
          <option value="OBJECT_DOWNLOAD">OBJECT_DOWNLOAD</option>
          <option value="OBJECT_DELETE">OBJECT_DELETE</option>
          <option value="OBJECT_METADATA_UPDATE">OBJECT_METADATA_UPDATE</option>
          <option value="SCHEMA_CREATE">SCHEMA_CREATE</option>
          <option value="SCHEMA_UPDATE">SCHEMA_UPDATE</option>
          <option value="SCHEMA_DELETE">SCHEMA_DELETE</option>
          <option value="USER_LOGIN">USER_LOGIN</option>
        </select>

        <button type="submit" className="primary-button">
          Apply Filter
        </button>

        {(actionFilter || usernameFilter) && (
          <button
            type="button"
            className="clear-filter-button"
            onClick={handleClearFilters}
          >
            Clear
          </button>
        )}
      </form>

      {/* Events Table Card */}
      <div className="section-card">
        <div className="section-header d-flex justify-content-between align-items-center">
          <div>
            <h3>Audit Events</h3>
            <p>Showing {events.length} recorded events</p>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner" />
            <span>Loading audit log records...</span>
          </div>
        ) : events.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📜</div>
            <h3>No audit events found</h3>
            <p>No actions have been recorded matching your criteria.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>User</th>
                  <th>Resource</th>
                  <th>Status</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {events.map((evt) => (
                  <tr key={evt.id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: '12px' }}>
                      {formatDate(evt.timestamp)}
                    </td>
                    <td>
                      <span className={`badge ${getActionBadgeClass(evt.action, evt.success)}`}>
                        {evt.action}
                      </span>
                    </td>
                    <td>
                      <strong style={{ fontSize: '13px' }}>
                        {evt.username ? `@${evt.username}` : `User #${evt.user_id || 'System'}`}
                      </strong>
                    </td>
                    <td>
                      <div className="small">
                        <span className="text-muted">{evt.resource_type || 'object'}: </span>
                        <strong>{evt.resource_id || `#${evt.object_id || 'N/A'}`}</strong>
                      </div>
                    </td>
                    <td>
                      {evt.success ? (
                        <span className="badge badge-success">SUCCESS</span>
                      ) : (
                        <span className="badge badge-danger">FAILED</span>
                      )}
                    </td>
                    <td>
                      {evt.details && Object.keys(evt.details).length > 0 ? (
                        <pre
                          style={{
                            margin: 0,
                            padding: '4px 8px',
                            background: 'var(--surface-soft)',
                            borderRadius: '4px',
                            fontSize: '11px',
                            maxWidth: '300px',
                            maxHeight: '60px',
                            overflowY: 'auto',
                          }}
                        >
                          {JSON.stringify(evt.details)}
                        </pre>
                      ) : (
                        <span className="text-muted small">-</span>
                      )}
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
