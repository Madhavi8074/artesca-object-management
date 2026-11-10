import React, { useState, useEffect } from 'react'
import type { ObjectItem, ShareLinkResponse } from '../types'
import { ApiClient } from '../services/api'

interface ShareModalProps {
  objectItem: ObjectItem | null
  onClose: () => void
}

export const ShareModal: React.FC<ShareModalProps> = ({ objectItem, onClose }) => {
  const [expiresIn, setExpiresIn] = useState<number>(3600)
  const [shareData, setShareData] = useState<ShareLinkResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (objectItem) {
      loadShareLink(expiresIn)
    }
  }, [objectItem])

  const loadShareLink = async (expiry: number) => {
    if (!objectItem) return
    setLoading(true)
    setError(null)
    setCopied(false)
    try {
      const res = await ApiClient.getShareLink(objectItem.id, expiry)
      setShareData(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate share link')
    } finally {
      setLoading(false)
    }
  }

  const handleExpiryChange = (newExpiry: number) => {
    setExpiresIn(newExpiry)
    loadShareLink(newExpiry)
  }

  const handleCopy = () => {
    if (!shareData?.share_url) return
    navigator.clipboard.writeText(shareData.share_url)
    setCopied(true)
    setTimeout(() => setCopied(false), 3000)
  }

  if (!objectItem) return null

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ maxWidth: '540px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2>Share "{objectItem.filename}"</h2>
            <p style={{ margin: '3px 0 0', color: 'var(--text-secondary)', fontSize: '12px' }}>
              Generate a secure, time-limited presigned S3 download link
            </p>
          </div>
          <button type="button" className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body" style={{ padding: '20px' }}>
          <label style={{ display: 'block', marginBottom: '12px', fontWeight: 600, fontSize: '13px' }}>
            Link Expiration Period:
            <select
              value={expiresIn}
              onChange={(e) => handleExpiryChange(Number(e.target.value))}
              style={{ display: 'block', width: '100%', marginTop: '6px' }}
            >
              <option value={900}>15 Minutes</option>
              <option value={3600}>1 Hour (Recommended)</option>
              <option value={86400}>24 Hours (1 Day)</option>
              <option value={604800}>7 Days (Max)</option>
            </select>
          </label>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <div className="spinner" style={{ margin: '0 auto 10px' }} />
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                Generating cryptographic presigned signature...
              </span>
            </div>
          ) : error ? (
            <div className="error-box" style={{ margin: '15px 0' }}>{error}</div>
          ) : shareData ? (
            <div>
              <div style={{ margin: '14px 0 8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                Direct Presigned Download URL:
              </div>
              <div
                style={{
                  display: 'flex',
                  gap: '8px',
                  alignItems: 'center',
                }}
              >
                <input
                  type="text"
                  readOnly
                  value={shareData.share_url}
                  style={{
                    flex: 1,
                    fontFamily: 'monospace',
                    fontSize: '11px',
                    padding: '8px 10px',
                    background: 'var(--surface-soft)',
                  }}
                  onClick={(e) => (e.target as HTMLInputElement).select()}
                />
                <button
                  type="button"
                  className="primary-button"
                  style={{ whiteSpace: 'nowrap', padding: '8px 16px' }}
                  onClick={handleCopy}
                >
                  {copied ? '✓ Copied!' : 'Copy'}
                </button>
              </div>

              <div
                style={{
                  marginTop: '16px',
                  padding: '12px',
                  background: 'var(--surface-soft)',
                  borderRadius: '6px',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  lineHeight: '1.5',
                }}
              >
                🔒 <strong>Zero Credential Exposure:</strong> S3 secret access keys never leave the server.
                The recipient downloads directly from the storage endpoint using an expiring HMAC-SHA256 signature.
              </div>
            </div>
          ) : null}
        </div>

        <div className="modal-footer" style={{ display: 'flex', justifyContent: 'flex-end', padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

