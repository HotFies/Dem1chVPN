import { useState, useEffect } from 'react';
import { getSettings, toggleFeature, type Settings } from '../api/client';

/* Icons */
const cloudIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />
  </svg>
);

const shieldIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const messageIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
  </svg>
);

const copyIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
    <rect x="9" y="9" width="13" height="13" rx="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
);

export default function WarpToggle() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await getSettings();
      setSettings(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (feature: 'warp' | 'adguard' | 'mtproto') => {
    if (toggling) return;
    setToggling(feature);

    try {
      const result = await toggleFeature(feature);
      setSettings((prev) =>
        prev
          ? {
              ...prev,
              [`${feature}_enabled`]: result.enabled,
            }
          : null,
      );
    } catch (err) {
      console.error(`Failed to toggle ${feature}:`, err);
    } finally {
      setToggling(null);
    }
  };

  const handleCopy = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(key);
      setTimeout(() => setCopied(null), 1500);
    } catch {}
  };

  if (loading) {
    return (
      <div className="loading-page">
        <div className="spinner" />
        <span>Загрузка настроек...</span>
      </div>
    );
  }

  if (!settings) {
    return <div className="error">Ошибка загрузки настроек</div>;
  }

  const features = [
    {
      key: 'warp' as const,
      label: 'Cloudflare WARP',
      description: 'Double-hop: скрывает IP VPS через Cloudflare',
      enabled: settings.warp_enabled,
      icon: cloudIcon,
      color: 'var(--cyan)',
      dimColor: 'var(--cyan-dim)',
    },
    {
      key: 'adguard' as const,
      label: 'AdGuard Home',
      description: 'Блокировка рекламы и трекеров на DNS',
      enabled: settings.adguard_enabled,
      icon: shieldIcon,
      color: 'var(--emerald)',
      dimColor: 'var(--emerald-dim)',
    },
    {
      key: 'mtproto' as const,
      label: 'MTProto Прокси',
      description: 'Прокси для стабильной работы Telegram',
      enabled: settings.mtproto_enabled,
      icon: messageIcon,
      color: 'var(--violet)',
      dimColor: 'var(--violet-dim)',
    },
  ];

  return (
    <div className="warp-toggle">
      <h3>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="20" height="20" style={{ color: 'var(--cyan)' }}>
          <rect x="2" y="2" width="20" height="20" rx="5" />
          <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
          <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
        </svg>
        Дополнительные модули
      </h3>

      <div className="feature-list">
        {features.map((f) => (
          <div
            key={f.key}
            className={`feature-item ${f.enabled ? 'enabled' : ''}`}
            style={f.enabled ? { borderColor: `${f.color}22` } : undefined}
          >
            <div className="feature-info">
              <div className="feature-label" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  display: 'inline-flex', width: 28, height: 28,
                  alignItems: 'center', justifyContent: 'center',
                  borderRadius: 8, background: f.dimColor, color: f.color,
                }}>{f.icon}</span>
                {f.label}
              </div>
              <div className="feature-desc">{f.description}</div>
            </div>
            <label className="toggle-switch">
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
    </div>
  );
}
