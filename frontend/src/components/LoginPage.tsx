import React, { useState } from 'react'

interface LoginPageProps {
  onLogin: (username: string, password: string) => Promise<void>
  onRegister: (
    username: string,
    password: string,
    email?: string,
    displayName?: string,
    department?: string,
  ) => Promise<void>
  loading: boolean
  error: string | null
}

export const LoginPage: React.FC<LoginPageProps> = ({
  onLogin,
  onRegister,
  loading,
  error,
}) => {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [department, setDepartment] = useState('Engineering')
  const [localError, setLocalError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    if (mode === 'register') {
      if (password !== confirmPassword) {
        setLocalError('Passwords do not match')
        return
      }
      if (password.length < 6) {
        setLocalError('Password must be at least 6 characters long')
        return
      }
      onRegister(username, password, email, displayName, department)
    } else {
      onLogin(username, password)
    }
  }

  const activeError = localError || error

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="brand-large">
          <div className="brand-logo" style={{ width: '48px', height: '48px', fontSize: '24px' }}>
            ⚡
          </div>
          <div>
            <h1>EasyStore</h1>
            <p>S3-Compatible Object & Metadata Management</p>
          </div>
        </div>

        {/* Tab switch between Sign In and Register */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: '20px' }}>
          <button
            type="button"
            onClick={() => {
              setMode('login')
              setLocalError(null)
            }}
            style={{
              flex: 1,
              padding: '10px',
              background: 'none',
              border: 'none',
              borderBottom: mode === 'login' ? '2px solid var(--primary)' : 'none',
              color: mode === 'login' ? 'var(--primary)' : 'var(--text-secondary)',
              fontWeight: 600,
              cursor: 'pointer',
              fontSize: '14px',
            }}
            id="tab-sign-in"
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register')
              setLocalError(null)
            }}
            style={{
              flex: 1,
              padding: '10px',
              background: 'none',
              border: 'none',
              borderBottom: mode === 'register' ? '2px solid var(--primary)' : 'none',
              color: mode === 'register' ? 'var(--primary)' : 'var(--text-secondary)',
              fontWeight: 600,
              cursor: 'pointer',
              fontSize: '14px',
            }}
            id="tab-register"
          >
            Create Account
          </button>
        </div>

        <div className="login-heading">
          <h2>{mode === 'login' ? 'Sign In' : 'Create New Account'}</h2>
          <p>
            {mode === 'login'
              ? 'Access your object storage catalog and compliance dashboard'
              : 'Register a new account to access object management features'}
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <label>
            Username *
            <input
              type="text"
              required
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. madhavi"
              id="login-username-input"
            />
          </label>

          {mode === 'register' && (
            <>
              <label>
                Full Name / Display Name
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. Madhavi"
                  id="register-displayname-input"
                />
              </label>

              <label>
                Email Address
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. madhavi@easystore.local"
                  id="register-email-input"
                />
              </label>

              <label>
                Department
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  placeholder="e.g. Engineering"
                  id="register-department-input"
                />
              </label>
            </>
          )}

          <label>
            Password *
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === 'register' ? 'Minimum 6 characters' : 'Enter your password'}
              id="login-password-input"
            />
          </label>

          {mode === 'register' && (
            <label>
              Confirm Password *
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your password"
                id="register-confirm-password-input"
              />
            </label>
          )}

          {activeError && <div className="error-box">{activeError}</div>}

          <button
            type="submit"
            className="primary-button login-button"
            disabled={loading}
            id="login-submit-btn"
          >
            {loading
              ? mode === 'login'
                ? 'Authenticating...'
                : 'Creating Account...'
              : mode === 'login'
                ? 'Sign In to EasyStore'
                : 'Register & Sign In'}
          </button>
        </form>

        <div className="login-footer">
          EasyStore Object Management System &bull; Scality ARTESCA & MinIO S3 Compatible
        </div>
      </div>
    </div>
  )
}
