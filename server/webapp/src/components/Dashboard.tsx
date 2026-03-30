import React, { useState, useEffect } from 'react'

interface ServerStatus {
  cpu: number
  ram_used: number
  ram_total: number
  disk_used: number
  disk_total: number
  uptime: string
  xray_running: boolean
  xray_version: string
  users_count: number
  traffic_today_up: number
  traffic_today_down: number
}

function formatBytes(bytes: number): string {
  if (bytes >= 1024 ** 3) return (bytes / 1024 ** 3).toFixed(1) + ' GB'
  if (bytes >= 1024 ** 2) return (bytes / 1024 ** 2).toFixed(0) + ' MB'
  if (bytes >= 1024) return (bytes / 1024).toFixed(0) + ' KB'
  return `${bytes} B`
}

function ProgressBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0
  return (
    <div className="progress-bar">
      <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
      <span className="progress-text">{pct.toFixed(0)}%</span>
    </div>
  )
}

export default function Dashboard() {
  const [status, setStatus] = useState<ServerStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/status')
      .then(r => r.json())
      .then(data => { setStatus(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">⏳ Загрузка...</div>
  if (!status) return <div className="error">❌ Не удалось загрузить данные</div>

  return (
    <div className="dashboard">
      <div className="card xray-status">
        <div className="card-header">
          <span>🌐 Xray</span>
          <span className={`status-badge ${status.xray_running ? 'active' : 'inactive'}`}>
            {status.xray_running ? '🟢 Работает' : '🔴 Остановлен'}
          </span>
        </div>
        <div className="card-body">
          <div className="stat-row">
            <span>Версия</span><span>v{status.xray_version}</span>
          </div>
          <div className="stat-row">
            <span>Пользователей</span><span>{status.users_count}</span>
          </div>
          <div className="stat-row">
            <span>Uptime</span><span>{status.uptime}</span>
          </div>
        </div>
      </div>

      <div className="card server-stats">
        <div className="card-header">🖥️ Сервер</div>
        <div className="card-body">
          <div className="stat-item">
            <span>CPU</span>
            <ProgressBar value={status.cpu} max={100} color="#6c63ff" />
          </div>
          <div className="stat-item">
            <span>RAM</span>
            <ProgressBar value={status.ram_used} max={status.ram_total} color="#48c9b0" />
            <small>{formatBytes(status.ram_used)} / {formatBytes(status.ram_total)}</small>
          </div>
          <div className="stat-item">
            <span>Disk</span>
            <ProgressBar value={status.disk_used} max={status.disk_total} color="#e94560" />
            <small>{formatBytes(status.disk_used)} / {formatBytes(status.disk_total)}</small>
          </div>
        </div>
      </div>

      <div className="card traffic-today">
        <div className="card-header">📈 Трафик сегодня</div>
        <div className="card-body traffic-grid">
          <div className="traffic-item upload">
            <span className="traffic-label">↑ Upload</span>
            <span className="traffic-value">{formatBytes(status.traffic_today_up)}</span>
          </div>
          <div className="traffic-item download">
            <span className="traffic-label">↓ Download</span>
            <span className="traffic-value">{formatBytes(status.traffic_today_down)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
