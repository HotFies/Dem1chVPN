import React, { useState, useEffect, useCallback } from 'react'
import { getUsers, getUserLink, toggleUser, formatBytes, type User } from '../api/client'

/* ── Icons ── */
const linkIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
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

const copyIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
    <rect x="9" y="9" width="13" height="13" rx="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
)

const checkIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="var(--emerald)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
    <polyline points="20 6 9 17 4 12" />
  </svg>
)

const closeIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
)


/* ── Modal Overlay ── */
function LinkModal({
  user,
  vlessUrl,
  subUrl,
  onClose,
}: {
  user: User
  vlessUrl: string
  subUrl: string
  onClose: () => void
}) {
  const [copied, setCopied] = useState<string | null>(null)

  const handleCopy = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(key)
      setTimeout(() => setCopied(null), 1500)
    } catch {}
  }

  return (
    <div className="overlay-backdrop" onClick={onClose}>
      <div className="overlay-content" onClick={e => e.stopPropagation()}>
        <div className="overlay-header">
          <h3>🔗 Ссылки: {user.name}</h3>
          <button className="overlay-close" onClick={onClose}>{closeIcon}</button>
        </div>

        <div className="link-section">
          <span className="link-label">📡 Подписка (рекомендуется)</span>
          <div className="link-row">
            <code className="link-value">{subUrl}</code>
            <button className="btn-copy" onClick={() => handleCopy(subUrl, 'sub')}>
              {copied === 'sub' ? checkIcon : copyIcon}
            </button>
          </div>
        </div>

        <div className="link-section">
          <span className="link-label">🔗 Прямая ссылка VLESS</span>
          <div className="link-row">
            <code className="link-value">{vlessUrl}</code>
            <button className="btn-copy" onClick={() => handleCopy(vlessUrl, 'vless')}>
              {copied === 'vless' ? checkIcon : copyIcon}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Main Component ── */
export default function UserList() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<{
    type: 'link'
    user: User
    vlessUrl: string
    subUrl: string
  } | null>(null)
  const [toggling, setToggling] = useState<number | null>(null)

  useEffect(() => {
    getUsers()
      .then(data => { setUsers(data.users || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const handleLink = useCallback(async (user: User) => {
    try {
      const data = await getUserLink(user.id)
      setModal({ type: 'link', user, vlessUrl: data.vless_url, subUrl: data.sub_url })
    } catch (err) {
      console.error('Failed to get link:', err)
    }
  }, [])



  const handleToggle = useCallback(async (user: User) => {
    if (toggling !== null) return
    setToggling(user.id)
    try {
      const result = await toggleUser(user.id)
      setUsers(prev =>
        prev.map(u => u.id === user.id ? { ...u, active: result.active } : u)
      )
    } catch (err) {
      console.error('Failed to toggle:', err)
    } finally {
      setToggling(null)
    }
  }, [toggling])

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
                <button className="btn-sm btn-link-action" onClick={() => handleLink(u)}>
                  {linkIcon} <span>Ссылка</span>
                </button>

                <button
                  className={`btn-sm ${u.active ? 'btn-pause-action' : 'btn-play-action'}`}
                  onClick={() => handleToggle(u)}
                  disabled={toggling === u.id}
                >
                  {toggling === u.id ? (
                    <div className="spinner" style={{ width: 14, height: 14 }} />
                  ) : u.active ? (
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

      {/* Modals */}
      {modal?.type === 'link' && (
        <LinkModal
          user={modal.user}
          vlessUrl={modal.vlessUrl}
          subUrl={modal.subUrl}
          onClose={() => setModal(null)}
        />
      )}

    </div>
  )
}
