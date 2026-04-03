import React, { useState, useEffect } from 'react'
import { getSettings, toggleFeature, restartXray, updateGeo, createBackup, type Settings as SettingsType } from '../api/client'

/* ── Icons ── */
const settingsIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
)

const cloudIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />
  </svg>
)

const shieldIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
)

const messageIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
  </svg>
)

const refreshIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10" />
    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
  </svg>
)

const globeIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </svg>
)

const saveIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
    <polyline points="17 21 17 13 7 13 7 21" />
    <polyline points="7 3 7 8 15 8" />
  </svg>
)

const copyIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
    <rect x="9" y="9" width="13" height="13" rx="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
)

const featureIcons: Record<string, React.ReactNode> = {
  warp: cloudIcon,
  adguard: shieldIcon,
  mtproto: messageIcon,
}

const featureColors: Record<string, string> = {
  warp: 'var(--cyan)',
  adguard: 'var(--emerald)',
  mtproto: 'var(--violet)',
}

const featureDimColors: Record<string, string> = {
  warp: 'var(--cyan-dim)',
  adguard: 'var(--emerald-dim)',
  mtproto: 'var(--violet-dim)',
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsType | null>(null)
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    getSettings()
      .then(data => { setSettings(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  const handleToggle = async (feature: 'warp' | 'adguard' | 'mtproto') => {
    if (toggling) return
    setToggling(feature)
    try {
      const result = await toggleFeature(feature)
      // Use actual server response instead of optimistic toggle
      setSettings(prev =>
        prev ? { ...prev, [`${feature}_enabled`]: result.enabled } : null
      )
    } catch (err: any) {
      const msg = err?.message || `Ошибка переключения ${feature}`
      console.error(`Toggle ${feature} failed:`, err)
      showToast(`❌ ${msg}`)
    } finally {
      setToggling(null)
    }
  }

  const handleAction = async (action: () => Promise<any>, name: string) => {
    setActionLoading(name)
    try {
      await action()
    } catch {} finally {
      setActionLoading(null)
    }
  }

  const handleCopy = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(key)
      setTimeout(() => setCopied(null), 1500)
    } catch {}
  }

  if (loading) return (
    <div className="loading-page">
      <div className="spinner" />
      <span>Загрузка настроек...</span>
    </div>
  )

  if (!settings) return <div className="error">Ошибка загрузки настроек</div>

  const features = [
    {
      key: 'warp' as const,
      title: 'Cloudflare WARP',
      desc: 'Double-hop приватность',
      enabled: settings.warp_enabled,
    },
    {
      key: 'adguard' as const,
      title: 'AdGuard Home',
      desc: 'Блокировка рекламы и трекеров',
      enabled: settings.adguard_enabled,
    },
    {
      key: 'mtproto' as const,
      title: 'MTProto Прокси',
      desc: 'Прокси для Telegram',
      enabled: settings.mtproto_enabled,
    },
  ]

  return (
    <div className="settings">
      <div className="section-header">
        <div className="section-icon">{settingsIcon}</div>
        <h2>Настройки</h2>
      </div>

      {/* Feature toggles */}
      <div className="settings-list">
        {features.map(f => (
          <div
            key={f.key}
            className={`setting-card ${f.enabled ? 'enabled' : ''}`}
            style={f.enabled ? { borderColor: `${featureColors[f.key]}22` } : undefined}
          >
            <div className="setting-info">
              <span
                className="setting-icon"
                style={{
                  background: featureDimColors[f.key],
                  color: featureColors[f.key],
                }}
              >
                {featureIcons[f.key]}
              </span>
              <div>
                <div className="setting-title">{f.title}</div>
                <div className="setting-desc">{f.desc}</div>
              </div>
            </div>
            <label className="toggle">
              <input
                type="checkbox"
                checked={f.enabled}
                disabled={toggling === f.key}
                onChange={() => handleToggle(f.key)}
              />
              <span className={`toggle-slider ${toggling === f.key ? 'toggling' : ''}`} />
            </label>
          </div>
        ))}
      </div>

      {/* Server info */}
      <div className="server-info">
        <div className="info-row">
          <span className="info-label">IP сервера</span>
          <button
            className="info-value"
            onClick={() => handleCopy(settings.server_ip, 'ip')}
            style={{ cursor: 'pointer', border: 'none', display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'var(--font-mono)' }}
            title="Скопировать"
          >
            {settings.server_ip}
            {copied === 'ip' ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="var(--emerald)" strokeWidth="2" width="12" height="12">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : copyIcon}
          </button>
        </div>
        <div className="info-row">
          <span className="info-label">SNI</span>
          <button
            className="info-value"
            onClick={() => handleCopy(settings.reality_sni, 'sni')}
            style={{ cursor: 'pointer', border: 'none', display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'var(--font-mono)' }}
            title="Скопировать"
          >
            {settings.reality_sni}
            {copied === 'sni' ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="var(--emerald)" strokeWidth="2" width="12" height="12">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : copyIcon}
          </button>
        </div>
      </div>

      {/* Action buttons */}
      <div className="settings-actions">
        <button
          className="btn-action"
          onClick={() => handleAction(restartXray, 'restart')}
          disabled={actionLoading !== null}
        >
          {actionLoading === 'restart' ? <div className="spinner" style={{ width: 18, height: 18 }} /> : refreshIcon}
          Перезапуск Xray
        </button>
        <button
          className="btn-action"
          onClick={() => handleAction(updateGeo, 'geo')}
          disabled={actionLoading !== null}
        >
          {actionLoading === 'geo' ? <div className="spinner" style={{ width: 18, height: 18 }} /> : globeIcon}
          Обновить гео-базы
        </button>
        <button
          className="btn-action"
          onClick={() => handleAction(createBackup, 'backup')}
          disabled={actionLoading !== null}
        >
          {actionLoading === 'backup' ? <div className="spinner" style={{ width: 18, height: 18 }} /> : saveIcon}
          Создать бэкап
        </button>
      </div>

      {/* Error toast */}
      {toast && (
        <div className="toast-error">{toast}</div>
      )}
    </div>
  )
}
