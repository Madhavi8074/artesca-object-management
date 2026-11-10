import React, { useState } from 'react'
import type { ObjectItem, SearchFilters, UserProfile, QueryGroup } from '../types'
import { formatBytes } from '../utils/formatters'
import { QueryBuilder } from './QueryBuilder'

interface SearchObjectsViewProps {
  objects: ObjectItem[]
  loading: boolean
  filters: SearchFilters
  currentPrefix?: string
  onFilterChange: <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => void
  onSearch: (e?: React.FormEvent) => void
  onClearFilters: () => void
  onVisualQuery: (group: QueryGroup) => void
  onViewObject: (id: number) => void
  onDownloadObject: (item: ObjectItem) => void
  onShareObject: (item: ObjectItem) => void
  onRequestDelete: (item: ObjectItem) => void
  onNavigateUpload: () => void
  onCreateFolder: () => void
  onSelectPrefix: (prefix: string) => void
  onReload: () => void
  userProfile: UserProfile | null
}

export const SearchObjectsView: React.FC<SearchObjectsViewProps> = ({
  objects,
  loading,
  filters,
  currentPrefix = '',
  onFilterChange,
  onSearch,
  onClearFilters,
  onVisualQuery,
  onViewObject,
  onDownloadObject,
  onShareObject,
  onRequestDelete,
  onNavigateUpload,
  onCreateFolder,
  onSelectPrefix,
  onReload,
  userProfile,
}) => {
  const [searchMode, setSearchMode] = useState<'standard' | 'visual'>('standard')
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Visual Query Builder State
  const [rootGroup, setRootGroup] = useState<QueryGroup>({
    combinator: 'AND',
    rules: [
      { field: 'filename', operator: 'contains', value: '' },
    ],
  })

  const canDelete =
    userProfile?.permissions.includes('OBJECT_DELETE') ||
    userProfile?.roles.includes('ADMIN') ||
    false

  const canUpload =
    userProfile?.permissions.includes('OBJECT_UPLOAD') ||
    userProfile?.roles.includes('ADMIN') ||
    userProfile?.roles.includes('EDITOR') ||
    true

  const hasActiveFilters =
    Boolean(
      filters.filename ||
        filters.object_key ||
        filters.object_key_regex ||
        filters.content_type ||
        filters.bucket ||
        (filters.size_operator !== 'none' && filters.size_value) ||
        filters.classification ||
        filters.department ||
        filters.project ||
        filters.document_type ||
        filters.author ||
        filters.description ||
        filters.custom_key ||
        filters.custom_value,
    )

  // Breadcrumbs calculation from currentPrefix
  const breadcrumbSegments = currentPrefix
    ? currentPrefix.split('/').filter(Boolean)
    : []

  return (
    <div className="page-content">
      {/* Page Header */}
      <div className="page-actions">
        <div>
          <h2>Object Explorer & Search</h2>
          <p>Explore S3 storage with virtual folders, visual AST queries, and JSONB metadata indexing.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            type="button"
            className="secondary-button"
            onClick={onReload}
            title="Refresh Object List"
            id="refresh-objects-btn"
          >
            🔄 Refresh
          </button>
          {canUpload && (
            <button
              type="button"
              className="secondary-button"
              onClick={onCreateFolder}
              title="Create Virtual Folder"
              id="new-folder-btn"
            >
              📁 New Folder
            </button>
          )}
          <button
            type="button"
            className="primary-button"
            onClick={onNavigateUpload}
            id="upload-shortcut-btn"
          >
            + Upload Object
          </button>
        </div>
      </div>

      {/* Folder Navigation Breadcrumbs */}
      <div
        className="section-card"
        style={{
          padding: '12px 18px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '13px',
        }}
      >
        <span style={{ color: 'var(--text-secondary)' }}>Location:</span>
        <button
          type="button"
          onClick={() => onSelectPrefix('')}
          style={{
            background: 'none',
            border: 'none',
            color: !currentPrefix ? 'var(--text)' : 'var(--primary)',
            fontWeight: !currentPrefix ? 700 : 500,
            cursor: 'pointer',
            padding: '2px 4px',
          }}
        >
          Root /
        </button>

        {breadcrumbSegments.map((segment, idx) => {
          const pathUpTo = breadcrumbSegments.slice(0, idx + 1).join('/') + '/'
          const isLast = idx === breadcrumbSegments.length - 1
          return (
            <React.Fragment key={pathUpTo}>
              <span style={{ color: 'var(--border)' }}>&gt;</span>
              <button
                type="button"
                onClick={() => onSelectPrefix(pathUpTo)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: isLast ? 'var(--text)' : 'var(--primary)',
                  fontWeight: isLast ? 700 : 500,
                  cursor: isLast ? 'default' : 'pointer',
                  padding: '2px 4px',
                }}
              >
                📁 {segment}
              </button>
            </React.Fragment>
          )
        })}
      </div>

      {/* Mode Switcher */}
      <div className="mode-toggle-card mb-3">
        <div className="btn-group">
          <button
            type="button"
            className={`btn ${searchMode === 'standard' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSearchMode('standard')}
          >
            Standard Search Filters
          </button>
          <button
            type="button"
            className={`btn ${searchMode === 'visual' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSearchMode('visual')}
          >
            Visual AND/OR/NOT Query Builder
          </button>
        </div>
      </div>

      {/* Visual Query Builder Mode */}
      {searchMode === 'visual' ? (
        <div className="section-card mb-4">
          <QueryBuilder
            rootGroup={rootGroup}
            onChange={setRootGroup}
            onExecute={() => onVisualQuery(rootGroup)}
            loading={loading}
          />
        </div>
      ) : (
        /* Standard Filter Bar */
        <form onSubmit={onSearch}>
          <div className="filter-card">
            <div className="search-wrapper">
              <span>🔍</span>
              <input
                type="text"
                placeholder="Search filename or object key..."
                value={filters.filename}
                onChange={(e) => onFilterChange('filename', e.target.value)}
                id="search-filename-input"
              />
            </div>

            <select
              value={filters.classification}
              onChange={(e) => onFilterChange('classification', e.target.value)}
              id="filter-classification-select"
            >
              <option value="">Classification: Any</option>
              <option value="PUBLIC">PUBLIC</option>
              <option value="INTERNAL">INTERNAL</option>
              <option value="CONFIDENTIAL">CONFIDENTIAL</option>
              <option value="RESTRICTED">RESTRICTED</option>
            </select>

            <input
              type="text"
              placeholder="Department..."
              value={filters.department}
              onChange={(e) => onFilterChange('department', e.target.value)}
              style={{ width: '150px' }}
            />

            <input
              type="text"
              placeholder="Project..."
              value={filters.project}
              onChange={(e) => onFilterChange('project', e.target.value)}
              style={{ width: '150px' }}
            />

            <button type="submit" className="primary-button" id="search-submit-btn">
              Search
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? '▲ Less Filters' : '▼ More Filters'}
            </button>

            {hasActiveFilters && (
              <button
                type="button"
                className="secondary-button"
                onClick={onClearFilters}
                title="Reset all filters"
              >
                Clear
              </button>
            )}
          </div>

          {/* Advanced Filters Expandable Drawer */}
          {showAdvanced && (
            <div
              className="section-card"
              style={{ marginBottom: '20px', padding: '20px 22px' }}
            >
              <h4 style={{ margin: '0 0 16px', fontSize: '14px', color: 'var(--text)' }}>
                Advanced Search Criteria
              </h4>

              <div className="form-grid" style={{ padding: 0 }}>
                <label>
                  Object Key Pattern
                  <input
                    type="text"
                    placeholder="e.g. project-a/"
                    value={filters.object_key}
                    onChange={(e) => onFilterChange('object_key', e.target.value)}
                  />
                </label>

                <label>
                  Object Key Regex (POSIX)
                  <input
                    type="text"
                    placeholder="e.g. \\.pdf$"
                    value={filters.object_key_regex}
                    onChange={(e) => onFilterChange('object_key_regex', e.target.value)}
                  />
                </label>

                <label>
                  Bucket Name
                  <input
                    type="text"
                    placeholder="e.g. artesca-documents"
                    value={filters.bucket}
                    onChange={(e) => onFilterChange('bucket', e.target.value)}
                  />
                </label>

                <label>
                  Document Type
                  <input
                    type="text"
                    placeholder="e.g. Technical Spec"
                    value={filters.document_type}
                    onChange={(e) => onFilterChange('document_type', e.target.value)}
                  />
                </label>

                <label>
                  Author
                  <input
                    type="text"
                    placeholder="e.g. Madhavi"
                    value={filters.author}
                    onChange={(e) => onFilterChange('author', e.target.value)}
                  />
                </label>

                <label>
                  Description Keywords
                  <input
                    type="text"
                    placeholder="Search description..."
                    value={filters.description}
                    onChange={(e) => onFilterChange('description', e.target.value)}
                  />
                </label>

                <label>
                  Size Condition
                  <select
                    value={filters.size_operator}
                    onChange={(e) =>
                      onFilterChange(
                        'size_operator',
                        e.target.value as SearchFilters['size_operator'],
                      )
                    }
                  >
                    <option value="none">Any Size</option>
                    <option value="greater">Greater than (&gt;)</option>
                    <option value="less">Less than (&lt;)</option>
                    <option value="equal">Equal to (=)</option>
                  </select>
                </label>

                <label>
                  Size in Bytes
                  <input
                    type="number"
                    placeholder="e.g. 50000"
                    value={filters.size_value}
                    onChange={(e) => onFilterChange('size_value', e.target.value)}
                  />
                </label>

                <label>
                  Custom Metadata JSON Key
                  <input
                    type="text"
                    placeholder="e.g. classification or project_code"
                    value={filters.custom_key}
                    onChange={(e) => onFilterChange('custom_key', e.target.value)}
                  />
                </label>

                <label>
                  Custom Metadata Value
                  <input
                    type="text"
                    placeholder="e.g. Secret or PRJ-9001"
                    value={filters.custom_value}
                    onChange={(e) => onFilterChange('custom_value', e.target.value)}
                  />
                </label>
              </div>
            </div>
          )}
        </form>
      )}

      {/* Results Table Section */}
      <div className="section-card">
        <div className="section-header d-flex justify-content-between align-items-center">
          <div>
            <h3>Objects Catalog</h3>
            <p>
              Showing {objects.length} matching item{objects.length === 1 ? '' : 's'}
            </p>
          </div>
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="spinner" />
            <span>Executing query and retrieving metadata records...</span>
          </div>
        ) : objects.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📁</div>
            <h3>No objects found in this view</h3>
            <p>Upload a file or create a folder to get started.</p>
            {hasActiveFilters && (
              <button
                type="button"
                className="secondary-button"
                style={{ marginTop: '12px' }}
                onClick={onClearFilters}
              >
                Clear All Filters
              </button>
            )}
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name & Key</th>
                  <th>Bucket</th>
                  <th>Size</th>
                  <th>Type</th>
                  <th>Classification</th>
                  <th>Department / Project</th>
                  <th>Custom Metadata</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {objects.map((item) => {
                  const isFolder = item.is_folder || item.content_type === 'application/x-directory' || item.object_key.endsWith('/')

                  return (
                    <tr key={item.id}>
                      <td>
                        <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
                          #{item.id}
                        </span>
                      </td>
                      <td>
                        <div
                          className="object-name"
                          style={{ cursor: isFolder ? 'pointer' : 'default' }}
                          onClick={() => {
                            if (isFolder) {
                              onSelectPrefix(item.object_key)
                            }
                          }}
                        >
                          <div className="file-icon" style={{ background: isFolder ? '#e2e8f0' : undefined }}>
                            {isFolder ? '📁' : (item.filename.split('.').pop() || 'FILE').toUpperCase().slice(0, 4)}
                          </div>
                          <div>
                            <strong style={{ color: isFolder ? 'var(--primary)' : 'inherit' }}>
                              {item.filename} {isFolder && '/'}
                            </strong>
                            <span title={item.object_key}>{item.object_key}</span>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="bucket-name">{item.bucket}</span>
                      </td>
                      <td>{isFolder ? '-' : formatBytes(item.size_bytes)}</td>
                      <td>
                        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                          {isFolder ? 'Folder' : (item.content_type || 'octet-stream')}
                        </span>
                      </td>
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
                        {item.metadata?.custom_metadata &&
                        Object.keys(item.metadata.custom_metadata).length > 0 ? (
                          <span
                            className="status-badge active"
                            style={{
                              cursor: 'pointer',
                              fontSize: '11px',
                              background: 'var(--primary-light)',
                              color: 'var(--primary)',
                            }}
                            onClick={() => onViewObject(item.id)}
                            title={JSON.stringify(item.metadata.custom_metadata, null, 2)}
                          >
                            {Object.keys(item.metadata.custom_metadata).length} tags
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>-</span>
                        )}
                      </td>
                      <td>
                        <div className="action-buttons">
                          {!isFolder && (
                            <>
                              <button
                                type="button"
                                className="icon-button"
                                onClick={() => onViewObject(item.id)}
                                title="View / Edit Metadata"
                              >
                                👁️ View
                              </button>
                              <button
                                type="button"
                                className="icon-button"
                                onClick={() => onDownloadObject(item)}
                                title="Download Object"
                              >
                                ⬇️ Get
                              </button>
                              <button
                                type="button"
                                className="icon-button"
                                onClick={() => onShareObject(item)}
                                title="Generate Presigned Share Link"
                              >
                                🔗 Share
                              </button>
                            </>
                          )}
                          {isFolder && (
                            <button
                              type="button"
                              className="icon-button"
                              onClick={() => onSelectPrefix(item.object_key)}
                              title="Open Folder"
                            >
                              📂 Open
                            </button>
                          )}
                          {canDelete && (
                            <button
                              type="button"
                              className="icon-button danger"
                              onClick={() => onRequestDelete(item)}
                              title="Delete Item"
                            >
                              🗑️
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
