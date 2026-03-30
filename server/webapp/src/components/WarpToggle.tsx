import { useState, useEffect } from 'react';
import { getSettings, toggleFeature, type Settings } from '../api/client';

/**
 * WarpToggle — Toggle switches for WARP, AdGuard, MTProto
 */
export default function WarpToggle() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<string | null>(null);

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

  if (loading) {
    return <div className="card loading-card">Загрузка настроек...</div>;
  }

  if (!settings) {
    return <div className="card error-card">Ошибка загрузки настроек</div>;
  }

  const features = [
    {
      key: 'warp' as const,
      label: '☁️ Cloudflare WARP',
      description: 'Double-hop: скрывает IP VPS через Cloudflare',
      enabled: settings.warp_enabled,
    },
    {
      key: 'adguard' as const,
      label: '🛡️ AdGuard Home',
      description: 'Блокировка рекламы и трекеров на уровне DNS',
      enabled: settings.adguard_enabled,
    },
    {
      key: 'mtproto' as const,
      label: '💬 MTProto Proxy',
      description: 'Прокси для Telegram при блокировке',
      enabled: settings.mtproto_enabled,
    },
  ];

  return (
    <div className="warp-toggle">
      <h3>⚙️ Дополнительные модули</h3>

      <div className="feature-list">
        {features.map((f) => (
          <div key={f.key} className="feature-item">
            <div className="feature-info">
              <div className="feature-label">{f.label}</div>
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
          <code className="info-value">{settings.server_ip}</code>
        </div>
        <div className="info-row">
          <span className="info-label">SNI</span>
          <code className="info-value">{settings.reality_sni}</code>
        </div>
      </div>
    </div>
  );
}
