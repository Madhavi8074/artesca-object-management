import React from 'react'
import type { UserProfile } from '../types'

interface TopbarProps {
  title: string
  subtitle: string
  userProfile: UserProfile | null
  dbConnected: boolean
}

export const Topbar: React.FC<TopbarProps> = ({
  title,
  subtitle,
  userProfile,
  dbConnected,
}) => {
  const initials = (userProfile?.username || 'U').slice(0, 2).toUpperCase()

  return (
    <header className="topbar">
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            className={`status-badge ${dbConnected ? 'active' : 'inactive'}`}
            title={dbConnected ? 'PostgreSQL & S3 Operational' : 'Database Disconnected'}
          >
            <span />
            {dbConnected ? 'Storage & DB Online' : 'System Offline'}
          </span>
        </div>

        <div className="topbar-user">
          <div className="avatar">{initials}</div>
          <div>
            <strong>{userProfile?.display_name || userProfile?.username || 'User'}</strong>
            <span>{userProfile?.department || 'Enterprise Ops'}</span>
          </div>
        </div>
      </div>
    </header>
  )
}
