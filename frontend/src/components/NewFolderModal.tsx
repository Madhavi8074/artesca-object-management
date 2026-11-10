import React, { useState } from 'react'

interface NewFolderModalProps {
  currentPrefix?: string
  bucket?: string
  onClose: () => void
  onCreate: (folderName: string) => Promise<void>
}

export const NewFolderModal: React.FC<NewFolderModalProps> = ({
  currentPrefix,
  onClose,
  onCreate,
}) => {
  const [folderName, setFolderName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const clean = folderName.trim().replace(/\/+/g, '')
    if (!clean) {
      setError('Please enter a valid folder name')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      await onCreate(clean)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create folder')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ maxWidth: '440px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>Create New Folder</h2>
            <p style={{ margin: '3px 0 0', color: 'var(--text-secondary)', fontSize: '12px' }}>
              {currentPrefix ? `Inside /${currentPrefix}` : 'In root directory'}
            </p>
          </div>
          <button type="button" className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body" style={{ padding: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 600, fontSize: '13px' }}>
              Folder Name:
              <input
                type="text"
                required
                autoFocus
                placeholder="e.g. documents, reports, logs"
                value={folderName}
                onChange={(e) => setFolderName(e.target.value)}
                style={{ display: 'block', width: '100%', marginTop: '6px' }}
              />
            </label>

            {error && <div className="error-box" style={{ margin: '12px 0 0' }}>{error}</div>}
          </div>

          <div
            className="modal-footer"
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '10px',
              padding: '16px 20px',
              borderTop: '1px solid var(--border)',
            }}
          >
            <button type="button" className="secondary-button" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="primary-button" disabled={submitting || !folderName.trim()}>
              {submitting ? 'Creating...' : '+ Create Folder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
