import React from 'react'
import type { UserProfile } from '../types'

export type NavTab = 'dashboard' | 'search' | 'upload' | 'audit' | 'schemas'

interface SidebarProps {
  activeTab: NavTab
  onSelectTab: (tab: NavTab) => void
  userProfile: UserProfile | null
  onLogout: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  userProfile,
  onLogout,
}) => {
  const hasAuditPermission =
    userProfile?.permissions.includes('AUDIT_READ') ||
    userProfile?.roles.includes('ADMIN') ||
    false

  const hasUploadPermission =
    userProfile?.permissions.includes('OBJECT_UPLOAD') ||
    userProfile?.roles.includes('ADMIN') ||
    userProfile?.roles.includes('EDITOR') ||
    false


  const primaryRole = userProfile?.roles[0] || 'USER'

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-logo">A</div>
        <div>
          <strong>ARTESCA</strong>
          <span>Object Management</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <button
          type="button"
          className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => onSelectTab('dashboard')}
          id="nav-dashboard-btn"
        >
          <span>📊</span>
          Dashboard
        </button>

        <button
          type="button"
          className={`nav-item ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => onSelectTab('search')}
          id="nav-search-btn"
        >
          <span>🔍</span>
          Objects & Search
        </button>

        {hasUploadPermission && (
          <button
            type="button"
            className={`nav-item ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => onSelectTab('upload')}
            id="nav-upload-btn"
          >
            <span>⬆️</span>
            Upload Object
          </button>
        )}

{userProfile?.roles.includes('ADMIN') && (
  <button
    type="button"
    className={`nav-item ${activeTab === 'schemas' ? 'active' : ''}`}
    onClick={() => onSelectTab('schemas')}
  >
    <span>🧩</span>
    Metadata Schemas
  </button>
)}

        {hasAuditPermission && (
          <button
            type="button"
            className={`nav-item ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => onSelectTab('audit')}
            id="nav-audit-btn"
          >
            <span>📜</span>
            Audit Trail
          </button>
        )}
      </nav>

      <div className="sidebar-bottom">
        <div className="permission-card">
          <div className="permission-dot" />
          <div>
            <strong>{userProfile?.display_name || userProfile?.username || 'User'}</strong>
            <span>Role: {primaryRole}</span>
          </div>
        </div>

        <button
          type="button"
          className="logout-button"
          onClick={onLogout}
          id="sidebar-logout-btn"
        >
          🚪 Sign out
        </button>
      </div>
    </aside>
  )
}
