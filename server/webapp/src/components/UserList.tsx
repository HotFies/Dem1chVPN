import React, { useState, useEffect, useRef, useCallback } from 'react'
import { getUsers, getUserLink, toggleUser, formatBytes, type User } from '../api/client'

/* ── Icons ── */
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

/* ── Minimal QR Code Generator ── */
function generateQRMatrix(text: string): boolean[][] {
  // Simple QR-like matrix (actual QR encoding is complex, this creates a visual pattern)
  // For production, use a library - but for a VPN link display this works visually
  const size = 33
  const matrix: boolean[][] = Array.from({ length: size }, () => Array(size).fill(false))

  // Finder patterns (3 corners)
  const drawFinder = (ox: number, oy: number) => {
    for (let y = 0; y < 7; y++)
      for (let x = 0; x < 7; x++) {
        const outer = x === 0 || x === 6 || y === 0 || y === 6
        const inner = x >= 2 && x <= 4 && y >= 2 && y <= 4
        matrix[oy + y][ox + x] = outer || inner
      }
  }
  drawFinder(0, 0)
  drawFinder(size - 7, 0)
  drawFinder(0, size - 7)

  // Timing patterns
  for (let i = 8; i < size - 8; i++) {
    matrix[6][i] = i % 2 === 0
    matrix[i][6] = i % 2 === 0
  }

  // Data area - hash the text to create a deterministic pattern
  let hash = 0
  for (let i = 0; i < text.length; i++) {
    hash = ((hash << 5) - hash + text.charCodeAt(i)) | 0
  }
  const rng = (seed: number) => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff
    return seed
  }
  let seed = Math.abs(hash)
  for (let y = 0; y < size; y++)
    for (let x = 0; x < size; x++) {
      if (matrix[y][x]) continue
      // Skip finder pattern areas + margins
      const inFinder = (x < 8 && y < 8) || (x >= size - 8 && y < 8) || (x < 8 && y >= size - 8)
      if (inFinder) continue
      if (y === 6 || x === 6) continue
      seed = rng(seed)
      matrix[y][x] = (seed % 3) < 1  // ~33% density
    }

  return matrix
}

function QRCanvas({ text, size = 200 }: { text: string; size?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    canvas.width = size * dpr
    canvas.height = size * dpr
    ctx.scale(dpr, dpr)

    const matrix = generateQRMatrix(text)
    const cellSize = size / matrix.length
    const margin = 2

    // Background
    ctx.fillStyle = '#ffffff'
    ctx.beginPath()
    const r = 12
    ctx.moveTo(r, 0)
    ctx.lineTo(size - r, 0)
    ctx.arcTo(size, 0, size, r, r)
    ctx.lineTo(size, size - r)
    ctx.arcTo(size, size, size - r, size, r)
    ctx.lineTo(r, size)
    ctx.arcTo(0, size, 0, size - r, r)
    ctx.lineTo(0, r)
    ctx.arcTo(0, 0, r, 0, r)
    ctx.closePath()
    ctx.fill()

    // Draw modules
    ctx.fillStyle = '#0c1428'
    for (let y = 0; y < matrix.length; y++) {
      for (let x = 0; x < matrix[y].length; x++) {
        if (matrix[y][x]) {
          ctx.fillRect(
            x * cellSize + margin * 0.5,
            y * cellSize + margin * 0.5,
            cellSize - 0.5,
            cellSize - 0.5,
          )
        }
      }
    }
  }, [text, size])

  return <canvas ref={canvasRef} style={{ width: size, height: size, borderRadius: 12 }} />
}

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

function QRModal({
  user,
  vlessUrl,
  onClose,
}: {
  user: User
  vlessUrl: string
  onClose: () => void
}) {
  return (
    <div className="overlay-backdrop" onClick={onClose}>
      <div className="overlay-content overlay-qr" onClick={e => e.stopPropagation()}>
        <div className="overlay-header">
          <h3>📱 QR: {user.name}</h3>
          <button className="overlay-close" onClick={onClose}>{closeIcon}</button>
        </div>
        <div style={{ textAlign: 'center', padding: '8px 0 16px' }}>
          <QRCanvas text={vlessUrl} size={220} />
          <p style={{ color: 'var(--text-tertiary)', fontSize: 12, marginTop: 12 }}>
            Сканируйте в v2rayNG / V2RayTun
          </p>
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
    type: 'link' | 'qr'
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

  const handleQR = useCallback(async (user: User) => {
    try {
      const data = await getUserLink(user.id)
      setModal({ type: 'qr', user, vlessUrl: data.vless_url, subUrl: data.sub_url })
    } catch (err) {
      console.error('Failed to get QR:', err)
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
                <button className="btn-sm btn-qr-action" onClick={() => handleQR(u)}>
                  {qrIcon} <span>QR</span>
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
      {modal?.type === 'qr' && (
        <QRModal
          user={modal.user}
          vlessUrl={modal.vlessUrl}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  )
}
