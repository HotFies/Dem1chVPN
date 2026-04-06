import React, { useState, useEffect } from 'react'
import { getServerStatus, formatBytes, formatPercent, type ServerStatus } from '../api/client'


function CircularGauge({ value, max, color, label }: {
  value: number; max: number; color: string; label: string
}) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0
  const radius = 26
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (pct / 100) * circumference

  return (
    <div className="gauge-card">
      <svg className="gauge-svg" viewBox="0 0 64 64">
        {/* Трек */}
        <circle
          cx="32" cy="32" r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="5"
        />
        {/* Заполнение */}
        <circle
          cx="32" cy="32" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 32 32)"
          style={{
            transition: 'stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1)',
            filter: `drop-shadow(0 0 4px ${color}40)`,
          }}
        />
        {/* Проценты */}
        <text
          x="32" y="34"
          textAnchor="middle"
          fill="currentColor"
          fontSize="12"
          fontFamily="var(--font-mono)"
          fontWeight="600"
        >
          {pct.toFixed(0)}%
        </text>
      </svg>
      <div className="gauge-label">{label}</div>
    </div>
  )
}


const globeIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="20" height="20">
    <circle cx="12" cy="12" r="10" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </svg>
)

const serverIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <rect x="2" y="2" width="20" height="8" rx="2" />
    <rect x="2" y="14" width="20" height="8" rx="2" />
    <line x1="6" y1="6" x2="6.01" y2="6" />
    <line x1="6" y1="18" x2="6.01" y2="18" />
  </svg>
)

const trendingUpIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="18" height="18">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
    <polyline points="17 6 23 6 23 12" />
  </svg>
)

export default function Dashboard() {
  const [status, setStatus] = useState<ServerStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getServerStatus()
      .then(data => { setStatus(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="loading-page">
      <div className="spinner" />
      <span>Загрузка панели...</span>
    </div>
  )

  if (!status) return (
    <div className="error">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="32" height="32" style={{ margin: '0 auto 8px', display: 'block', opacity: 0.5 }}>
        <circle cx="12" cy="12" r="10" />
        <line x1="15" y1="9" x2="9" y2="15" />
        <line x1="9" y1="9" x2="15" y2="15" />
      </svg>
      Не удалось загрузить данные
    </div>
  )

  const ramPercent = formatPercent(status.ram_used, status.ram_total)
  const diskPercent = formatPercent(status.disk_used, status.disk_total)

  return (
    <div className="dashboard">
      {/* Карточка статуса */}
      <div className={`hero-status ${status.xray_running ? 'active-glow' : ''}`}>
        <div className="hero-top">
          <div className="hero-title">
            {globeIcon}
            <span>Xray Core</span>
          </div>
          <span className={`status-badge ${status.xray_running ? 'active' : 'inactive'}`}>
            <span className="status-dot" />
            {status.xray_running ? 'Работает' : 'Остановлен'}
          </span>
        </div>
        <div className="hero-info-chips">
          <span className="info-chip">v{status.xray_version}</span>
          <span className="info-chip">{status.users_count} пользоват.</span>
          <span className="info-chip">{status.uptime}</span>
        </div>
      </div>

      {/* Стата сервака — круговые графики */}
      <div className="stats-row">
        <CircularGauge value={status.cpu} max={100} color="#00d4ff" label="CPU" />
        <CircularGauge
          value={status.ram_used} max={status.ram_total}
          color="#7c3aed" label="RAM"
        />
        <CircularGauge
          value={status.disk_used} max={status.disk_total}
          color="#10b981" label="Диск"
        />
      </div>

      {/* Подробные ресурсы с прогресс-барами */}
      <div className="card">
        <div className="card-header">
          <span className="card-header-icon">{serverIcon}</span>
          <span style={{ flex: 1 }}>Ресурсы сервера</span>
        </div>
        <div className="card-body">
          <div className="resource-item">
            <div className="stat-row">
              <span>Оперативная память</span>
              <span>{formatBytes(status.ram_used)} / {formatBytes(status.ram_total)}</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${ramPercent}%`,
                  background: ramPercent > 80
                    ? 'linear-gradient(90deg, #ff4757, #ff6b81)'
                    : 'linear-gradient(90deg, #7c3aed, #a78bfa)',
                }}
              />
            </div>
          </div>
          <div className="resource-item" style={{ marginTop: 12 }}>
            <div className="stat-row">
              <span>Хранилище</span>
              <span>{formatBytes(status.disk_used)} / {formatBytes(status.disk_total)}</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${diskPercent}%`,
                  background: diskPercent > 80
                    ? 'linear-gradient(90deg, #ff4757, #ff6b81)'
                    : 'linear-gradient(90deg, #10b981, #34d399)',
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Трафик за сегодня */}
      <div className="card">
        <div className="card-header">
          <span className="card-header-icon">{trendingUpIcon}</span>
          <span style={{ flex: 1 }}>Трафик сегодня</span>
        </div>
        <div className="card-body traffic-grid">
          <div className="traffic-item upload">
            <span className="traffic-label">↑ исходящий</span>
            <span className="traffic-value">{formatBytes(status.traffic_today_up)}</span>
          </div>
          <div className="traffic-item download">
            <span className="traffic-label">↓ входящий</span>
            <span className="traffic-value">{formatBytes(status.traffic_today_down)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
