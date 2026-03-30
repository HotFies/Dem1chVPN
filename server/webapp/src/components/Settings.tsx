import React, { useState, useEffect } from 'react'
import { getSettings, toggleFeature, restartXray, updateGeo, createBackup } from '../api/client'

export default function Settings() {
  const [warpEnabled, setWarpEnabled] = useState(false)
  const [adguardEnabled, setAdguardEnabled] = useState(false)
  const [mtprotoEnabled, setMtprotoEnabled] = useState(false)

  useEffect(() => {
    getSettings()
      .then(data => {
        setWarpEnabled(data.warp_enabled || false)
        setAdguardEnabled(data.adguard_enabled || false)
        setMtprotoEnabled(data.mtproto_enabled || false)
      })
      .catch(() => {})
  }, [])

  const toggle = async (feature: 'warp' | 'adguard' | 'mtproto', current: boolean, setter: (v: boolean) => void) => {
    try {
      await toggleFeature(feature)
      setter(!current)
    } catch {}
  }

  return (
    <div className="settings">
      <div className="section-header"><h2>⚙️ Настройки</h2></div>

      <div className="settings-list">
        <div className="setting-card">
          <div className="setting-info">
            <span className="setting-icon">☁️</span>
            <div>
              <div className="setting-title">Cloudflare WARP</div>
              <div className="setting-desc">Double-hop приватность</div>
            </div>
          </div>
          <label className="toggle">
            <input type="checkbox" checked={warpEnabled}
                   onChange={() => toggle('warp', warpEnabled, setWarpEnabled)} />
            <span className="toggle-slider" />
          </label>
        </div>

        <div className="setting-card">
          <div className="setting-info">
            <span className="setting-icon">🛡️</span>
            <div>
              <div className="setting-title">AdGuard Home</div>
              <div className="setting-desc">Блокировка рекламы</div>
            </div>
          </div>
          <label className="toggle">
            <input type="checkbox" checked={adguardEnabled}
                   onChange={() => toggle('adguard', adguardEnabled, setAdguardEnabled)} />
            <span className="toggle-slider" />
          </label>
        </div>

        <div className="setting-card">
          <div className="setting-info">
            <span className="setting-icon">💬</span>
            <div>
              <div className="setting-title">MTProto Proxy</div>
              <div className="setting-desc">Прокси для Telegram</div>
            </div>
          </div>
          <label className="toggle">
            <input type="checkbox" checked={mtprotoEnabled}
                   onChange={() => toggle('mtproto', mtprotoEnabled, setMtprotoEnabled)} />
            <span className="toggle-slider" />
          </label>
        </div>
      </div>

      <div className="settings-actions">
        <button className="btn-action" onClick={() => restartXray()}>
          🔁 Перезапуск Xray
        </button>
        <button className="btn-action" onClick={() => updateGeo()}>
          🔄 Обновить гео-базы
        </button>
        <button className="btn-action" onClick={() => createBackup()}>
          💾 Создать бэкап
        </button>
      </div>
    </div>
  )
}
