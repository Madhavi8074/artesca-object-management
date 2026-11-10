import React, { useState } from 'react'
import type { ObjectItem } from '../types'
import { formatBytes } from '../utils/formatters'

interface DeleteConfirmModalProps {
  objectItem: ObjectItem | null
  onClose: () => void
  onConfirm: (id: number) => Promise<void>
}

export const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  objectItem,
  onClose,
  onConfirm,
}) => {
  const [deleting, setDeleting] = useState(false)

  if (!objectItem) return null

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await onConfirm(objectItem.id)
      onClose()
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ maxWidth: '520px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Confirm Object Deletion</h2>
          <button type="button" className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="delete-warning">
            <div className="warning-icon">⚠️</div>
            <div>
              <h3>Permanent Storage Deletion</h3>
              <p>
                This action will delete the file <strong>{objectItem.filename}</strong> (
                {formatBytes(objectItem.size_bytes)}) from bucket{' '}
                <code>{objectItem.bucket}</code> and remove all indexed metadata.
                This action cannot be undone.
              </p>
            </div>
          </div>

          <div
            style={{
              background: 'var(--surface-soft)',
              padding: '12px 14px',
              borderRadius: '8px',
              marginTop: '16px',
              fontSize: '12px',
            }}
          >
            <div>
              <span style={{ color: 'var(--text-secondary)' }}>Storage Key: </span>
              <code>{objectItem.object_key}</code>
            </div>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={onClose}
              disabled={deleting}
            >
              Cancel
            </button>
            <button
              type="button"
              className="danger-button"
              onClick={handleDelete}
              disabled={deleting}
              id="confirm-delete-btn"
            >
              {deleting ? 'Deleting from S3...' : 'Yes, Delete Object'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
