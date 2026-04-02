import React, { useState, useEffect } from 'react'
import { getUsers, formatBytes, type User } from '../api/client'

/* Icons */
const linkIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
  </svg>
)

const qrIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1" />
    <rect x="14" y="3" width="7" height="7" rx="1" />
    <rect x="3" y="14" width="7" height="7" rx="1" />
    <rect x="14" y="14" width="3" height="3" />
    <rect x="18" y="18" width="3" height="3" />
  </svg>
)

const toggleIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="1" y="5" width="22" height="14" rx="7" />
    <circle cx="16" cy="12" r="3" />
  </svg>
)

const usersIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </svg>
)

export default function UserList() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getUsers()
      .then(data => { setUsers(data.users || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="loading-page">
      <div className="spinner" />
      <span>Загрузка пользователей...</span>
    </div>
  )

  return (
    <div className="user-list">
      <div className="section-header">
        <div className="section-icon">{usersIcon}</div>
        <h2>Пользователи <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 14,
          color: 'var(--text-secondary)',
          fontWeight: 400,
          marginLeft: 4,
        }}>({users.length})</span></h2>
      </div>

      {users.length === 0 ? (
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="48" height="48" style={{ margin: '0 auto 12px', display: 'block', opacity: 0.3 }}>
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
          </svg>
          Нет пользователей
        </div>
      ) : (
        <div className="card-list">
          {users.map((u, i) => (
            <div
              key={u.id}
              className={`user-card ${u.active ? '' : 'disabled'}`}
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className="user-card-header">
                <span className={`user-status-dot ${u.active ? 'online' : 'offline'}`} />
                <span className="user-name">{u.name}</span>
              </div>

              <div className="user-card-body">
                <div className="stat-row">
                  <span>Трафик</span>
                  <span>{formatBytes(u.traffic_total)} / {u.traffic_limit ? formatBytes(u.traffic_limit) : '∞'}</span>
                </div>
                {u.traffic_limit && (
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${Math.min((u.traffic_total / u.traffic_limit) * 100, 100)}%`,
                        background: u.traffic_total > u.traffic_limit * 0.8
                          ? 'linear-gradient(90deg, #ff4757, #ff6b81)'
                          : 'linear-gradient(90deg, #00d4ff, #7c3aed)',
                      }}
                    />
                  </div>
                )}
                <div className="stat-row">
                  <span>Срок</span>
                  <span>{u.expiry || '∞ Бессрочно'}</span>
                </div>
              </div>

              <div className="user-card-actions">
                <button className="btn-sm">{linkIcon} <span>Ссылка</span></button>
                <button className="btn-sm">{qrIcon} <span>QR</span></button>
                <button className="btn-sm">
                  {u.active ? (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
                      <rect x="6" y="4" width="4" height="16" />
                      <rect x="14" y="4" width="4" height="16" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
