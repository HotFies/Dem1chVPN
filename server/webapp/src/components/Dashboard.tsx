import { motion, useReducedMotion } from 'framer-motion'
import {
  Globe,
  Server,
  TrendingUp,
  ArrowUp,
  ArrowDown,
  RefreshCw,
  XCircle,
} from 'lucide-react'
import { getServerStatus, formatBytes, formatPercent } from '../api/client'
import { StatusPill } from './ui/StatusPill'
import { IconButton } from './ui/IconButton'
import { Skeleton } from './ui/Skeleton'
import { usePollingQuery } from '../hooks/usePollingQuery'
import { useHaptic } from '../hooks/useHaptic'

function CircularGauge({ value, max, color, label }: { value: number; max: number; color: string; label: string }) {
  const reduceMotion = useReducedMotion()
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0
  const radius = 26
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (pct / 100) * circumference

  return (
    <div className="gauge-card">
      <svg className="gauge-svg" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5" />
        <motion.circle
          cx="32" cy="32" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={reduceMotion ? false : { strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ type: 'spring', stiffness: 80, damping: 22 }}
          transform="rotate(-90 32 32)"
        />
        <text x="32" y="34" textAnchor="middle" fill="currentColor" fontSize="12" fontFamily="var(--font-mono)" fontWeight="600">
          {pct.toFixed(0)}%
        </text>
      </svg>
      <div className="gauge-label">{label}</div>
    </div>
  )
}

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07, delayChildren: 0.04 } },
}
const item = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 260, damping: 24 } },
}

export default function Dashboard() {
  const h = useHaptic()
  const { data: status, loading, error, refreshing, refresh } = usePollingQuery(
    getServerStatus,
    [],
    { intervalMs: 10000 }
  )

  if (loading) {
    return (
      <div className="dashboard">
        <Skeleton height={104} radius="lg" />
        <div style={{ height: 12 }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {[0,1,2].map(i => <Skeleton key={i} height={104} radius="lg" />)}
        </div>
        <div style={{ height: 12 }} />
        <Skeleton height={140} radius="lg" />
        <div style={{ height: 12 }} />
        <Skeleton height={104} radius="lg" />
      </div>
    )
  }

  if (error || !status) {
    return (
      <div className="error">
        <XCircle size={32} style={{ margin: '0 auto 8px', display: 'block', opacity: 0.6 }} />
        Не удалось загрузить данные
        <div style={{ marginTop: 12 }}>
          <button type="button" className="ui-btn ui-btn--ghost ui-btn--sm" onClick={() => { h.impact('light'); refresh() }}>
            <RefreshCw size={14} /> Повторить
          </button>
        </div>
      </div>
    )
  }

  const ramPercent = formatPercent(status.ram_used, status.ram_total)
  const diskPercent = formatPercent(status.disk_used, status.disk_total)

  return (
    <motion.div className="dashboard" variants={stagger} initial="hidden" animate="show">
      {/* hero */}
      <motion.div variants={item} className={`hero-status ${status.xray_running ? 'active-glow' : ''}`}>
        <div className="hero-top">
          <div className="hero-title">
            <Globe size={20} strokeWidth={1.75} color="var(--accent)" />
            <span>Xray Core</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <StatusPill tone={status.xray_running ? 'active' : 'expired'}>
              {status.xray_running ? 'Работает' : 'Остановлен'}
            </StatusPill>
            <IconButton aria-label="Обновить" onClick={() => { h.impact('light'); refresh() }} size="sm" variant="plain">
              <motion.span animate={refreshing ? { rotate: 360 } : { rotate: 0 }} transition={{ duration: 0.9, repeat: refreshing ? Infinity : 0, ease: 'linear' }}>
                <RefreshCw size={16} strokeWidth={2} />
              </motion.span>
            </IconButton>
          </div>
        </div>
        <div className="hero-info-chips">
          <span className="info-chip">v{status.xray_version}</span>
          <span className="info-chip">{status.users_count} пользоват.</span>
          <span className="info-chip">{status.uptime}</span>
        </div>
      </motion.div>

      {/* gauges */}
      <motion.div variants={item} className="stats-row">
        <CircularGauge value={status.cpu} max={100} color="var(--accent)" label="CPU" />
        <CircularGauge value={status.ram_used} max={status.ram_total} color="var(--violet)" label="RAM" />
        <CircularGauge value={status.disk_used} max={status.disk_total} color="var(--success)" label="Диск" />
      </motion.div>

      {/* resources */}
      <motion.div variants={item} className="card">
        <div className="card-header">
          <span className="card-header-icon"><Server size={18} strokeWidth={1.75} /></span>
          <span style={{ flex: 1 }}>Ресурсы сервера</span>
        </div>
        <div className="card-body">
          <div className="resource-item">
            <div className="stat-row">
              <span>Оперативная память</span>
              <span className="num">{formatBytes(status.ram_used)} / {formatBytes(status.ram_total)}</span>
            </div>
            <div className="progress-bar">
              <motion.div
                className="progress-fill"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: Math.min(ramPercent / 100, 1) }}
                transition={{ type: 'spring', stiffness: 100, damping: 22, delay: 0.12 }}
                style={{
                  width: '100%',
                  transformOrigin: 'left center',
                  background: ramPercent > 80 ? 'linear-gradient(90deg, var(--danger), var(--danger-light))' : 'linear-gradient(90deg, var(--violet), var(--violet-light))',
                }}
              />
            </div>
          </div>
          <div className="resource-item" style={{ marginTop: 14 }}>
            <div className="stat-row">
              <span>Хранилище</span>
              <span className="num">{formatBytes(status.disk_used)} / {formatBytes(status.disk_total)}</span>
            </div>
            <div className="progress-bar">
              <motion.div
                className="progress-fill"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: Math.min(diskPercent / 100, 1) }}
                transition={{ type: 'spring', stiffness: 100, damping: 22, delay: 0.2 }}
                style={{
                  width: '100%',
                  transformOrigin: 'left center',
                  background: diskPercent > 80 ? 'linear-gradient(90deg, var(--danger), var(--danger-light))' : 'linear-gradient(90deg, var(--success), var(--success-light))',
                }}
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* traffic */}
      <motion.div variants={item} className="card">
        <div className="card-header">
          <span className="card-header-icon"><TrendingUp size={18} strokeWidth={1.75} /></span>
          <span style={{ flex: 1 }}>Трафик сегодня</span>
        </div>
        <div className="card-body traffic-grid">
          <div className="traffic-item upload">
            <span className="traffic-label"><ArrowUp size={12} strokeWidth={2.5} /> исходящий</span>
            <span className="traffic-value num">{formatBytes(status.traffic_today_up)}</span>
          </div>
          <div className="traffic-item download">
            <span className="traffic-label"><ArrowDown size={12} strokeWidth={2.5} /> входящий</span>
            <span className="traffic-value num">{formatBytes(status.traffic_today_down)}</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}
