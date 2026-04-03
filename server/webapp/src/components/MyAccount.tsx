import React, { useState, useEffect } from 'react';
import { getMyAccount, formatBytes, type MyAccount as MyAccountData } from '../api/client';

/* ── Icons ── */
const copyIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
);

const checkIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const externalLinkIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    <polyline points="15 3 21 3 21 9" />
    <line x1="10" y1="14" x2="21" y2="3" />
  </svg>
);

/* ── Copy Button ── */
function CopyBtn({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={copy} title="Копировать">
      {copied ? checkIcon : copyIcon}
      {label && <span>{copied ? 'Скопировано!' : label}</span>}
    </button>
  );
}

/** Open a deeplink — custom URL schemes (v2raytun://) need special handling */
function openDeeplink(url: string) {
  const isCustomScheme = !/^https?:\/\//i.test(url);
  if (isCustomScheme) {
    // Custom URL schemes (v2raytun://) — navigate directly so iOS opens the app
    window.location.href = url;
  } else {
    const tg = (window as any).Telegram?.WebApp;
    if (tg?.openLink) {
      tg.openLink(url);
    } else {
      window.open(url, '_blank');
    }
  }
}

/* ── Platform type ── */
type Platform = 'ios' | 'android' | 'windows' | 'macos' | 'router' | null;

const platformMeta: { id: Platform; icon: string; label: string }[] = [
  { id: 'ios', icon: '🍎', label: 'iOS' },
  { id: 'android', icon: '🤖', label: 'Android' },
  { id: 'windows', icon: '🖥️', label: 'Windows' },
  { id: 'macos', icon: '🍏', label: 'macOS' },
  { id: 'router', icon: '📡', label: 'Роутер' },
];

/* ── Date formatter ── */
function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '♾️ Бессрочно';
  const d = new Date(iso);
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function daysLeft(iso: string | null | undefined): string {
  if (!iso) return '';
  const now = new Date();
  const exp = new Date(iso);
  const diff = Math.ceil((exp.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  if (diff < 0) return 'истёк';
  if (diff === 0) return 'сегодня';
  // Russian plural: 1 день, 2-4 дня, 5-20 дней, 21 день, 22-24 дня...
  const mod10 = diff % 10;
  const mod100 = diff % 100;
  const word = (mod10 === 1 && mod100 !== 11) ? 'день'
    : (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) ? 'дня'
    : 'дней';
  return `${diff} ${word}`;
}

/* ══════════════════════════════════════════════════
   MyAccount Component
   ══════════════════════════════════════════════════ */

export default function MyAccount() {
  const [data, setData] = useState<MyAccountData | null>(null);
  const [loading, setLoading] = useState(true);
  const [platform, setPlatform] = useState<Platform>(null);
  const [linksOpen, setLinksOpen] = useState(true);

  useEffect(() => {
    getMyAccount()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  /* ── Loading state ── */
  if (loading) {
    return (
      <div className="my-account">
        <div className="loading-page">
          <div className="spinner" />
          <span>Загрузка...</span>
        </div>
      </div>
    );
  }

  /* ── No account ── */
  if (!data?.has_account) {
    return (
      <div className="my-account">
        <div className="ma-no-account">
          <div className="ma-no-account-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <h3>Нет VPN-аккаунта</h3>
          <p>Обратитесь к администратору для получения доступа к VPN.</p>
        </div>
      </div>
    );
  }

  const trafficPct = data.traffic_percent ?? 0;
  const isLimited = data.traffic_limit != null && data.traffic_limit > 0;
  const isExpired = data.expired;
  const isActive = data.active && !isExpired;

  /* progress bar color */
  const barColor = trafficPct > 90 ? 'var(--coral)' :
                   trafficPct > 70 ? 'var(--amber)' :
                   'var(--cyan)';

  return (
    <div className="my-account">

      {/* ═══ Hero Status Card ═══ */}
      <div className={`ma-hero ${isActive ? 'ma-hero--active' : 'ma-hero--inactive'}`}>
        <div className="ma-hero-top">
          <div className="ma-hero-user">
            <div className={`ma-avatar ${isActive ? 'active' : 'inactive'}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <div>
              <div className="ma-user-name">{data.name}</div>
              <div className="ma-user-since">с {fmtDate(data.created)}</div>
            </div>
          </div>
          <div className={`ma-status-pill ${isActive ? 'active' : isExpired ? 'expired' : 'blocked'}`}>
            <span className="ma-status-dot" />
            {isActive ? 'Активен' : isExpired ? 'Истёк' : 'Заблокирован'}
          </div>
        </div>

        {/* Expiry info */}
        {data.expiry && (
          <div className="ma-expiry-row">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
            </svg>
            <span>
              {isExpired
                ? `Срок истёк ${fmtDate(data.expiry)}`
                : <>Действует до <strong>{fmtDate(data.expiry)}</strong> <span className="ma-days-left">({daysLeft(data.expiry)})</span></>
              }
            </span>
          </div>
        )}
      </div>

      {/* ═══ Traffic Card ═══ */}
      <div className="ma-card">
        <div className="ma-card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          Трафик
        </div>

        <div className="ma-traffic-grid">
          <div className="ma-traffic-cell upload">
            <span className="ma-traffic-dir">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="12" height="12"><polyline points="17 11 12 6 7 11" /><line x1="12" y1="18" x2="12" y2="6" /></svg>
              Upload
            </span>
            <span className="ma-traffic-val">{formatBytes(data.traffic_up ?? 0)}</span>
          </div>
          <div className="ma-traffic-cell download">
            <span className="ma-traffic-dir">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="12" height="12"><polyline points="7 13 12 18 17 13" /><line x1="12" y1="6" x2="12" y2="18" /></svg>
              Download
            </span>
            <span className="ma-traffic-val">{formatBytes(data.traffic_down ?? 0)}</span>
          </div>
        </div>

        {/* Progress bar */}
        {isLimited && (
          <div className="ma-progress-wrap">
            <div className="ma-progress-info">
              <span>Использовано</span>
              <span className="ma-progress-nums">
                {formatBytes(data.traffic_total ?? 0)} / {formatBytes(data.traffic_limit!)}
              </span>
            </div>
            <div className="ma-progress-bar">
              <div
                className="ma-progress-fill"
                style={{
                  width: `${trafficPct}%`,
                  background: `linear-gradient(90deg, ${barColor}, ${barColor}dd)`,
                }}
              />
            </div>
            <div className="ma-progress-pct" style={{ color: barColor }}>{trafficPct}%</div>
          </div>
        )}
        {!isLimited && (
          <div className="ma-unlimited-badge">♾️ Безлимитный трафик</div>
        )}
      </div>

      {/* ═══ Quick Setup — Links ═══ */}
      <div className="ma-card">
        <button
          className="ma-card-toggle"
          onClick={() => setLinksOpen(!linksOpen)}
        >
          <div className="ma-card-title" style={{ marginBottom: 0 }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
            </svg>
            Подключение и ссылки
          </div>
          <svg className={`ma-chevron ${linksOpen ? 'open' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>

        {linksOpen && (
          <div className="ma-links-body">

            {/* Subscription URL */}
            {data.sub_url && (
              <div className="ma-link-block">
                <div className="ma-link-label">
                  <span className="ma-link-icon">📡</span>
                  Подписка (автообновление)
                </div>
                <div className="ma-link-row">
                  <code className="ma-link-value">{data.sub_url}</code>
                  <CopyBtn text={data.sub_url} />
                </div>
                <div className="ma-link-hint">v2rayN · v2rayNG · Streisand · V2Box</div>
              </div>
            )}

            {/* iOS Quick Import */}
            {data.sub_deeplink && (
              <div className="ma-link-block ma-ios-block">
                <div className="ma-link-label">
                  <span className="ma-link-icon">📱</span>
                  iOS — V2RayTun (быстрый импорт)
                </div>
                <button
                  className="ma-deeplink-btn"
                  onClick={() => openDeeplink(data.sub_deeplink!)}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  Импорт подписки
                </button>
                <div className="ma-link-row ma-link-row--compact">
                  <code className="ma-link-value ma-link-value--small">{data.sub_deeplink.length > 60 ? data.sub_deeplink.substring(0, 60) + '...' : data.sub_deeplink}</code>
                  <CopyBtn text={data.sub_deeplink} />
                </div>
              </div>
            )}

            {/* Routing deeplink for iOS */}
            {data.route_deeplink && (
              <div className="ma-link-block">
                <div className="ma-link-label">
                  <span className="ma-link-icon">🔀</span>
                  Маршрутизация — iOS
                </div>
                <button
                  className="ma-deeplink-btn ma-deeplink-btn--routing"
                  onClick={() => openDeeplink(data.route_deeplink!)}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
                    <path d="M8.59 13.51l6.83 3.98" /><path d="M15.41 6.51l-6.82 3.98" />
                  </svg>
                  Импорт маршрутов
                </button>
                <div className="ma-link-hint">Российские сайты — напрямую, остальное — через VPN</div>
              </div>
            )}

            {/* Direct VLESS Link */}
            {data.vless_url && (
              <div className="ma-link-block">
                <div className="ma-link-label">
                  <span className="ma-link-icon">🔗</span>
                  Прямая VLESS ссылка
                </div>
                <div className="ma-link-row">
                  <code className="ma-link-value ma-link-value--small">{data.vless_url.length > 60 ? data.vless_url.substring(0, 60) + '...' : data.vless_url}</code>
                  <CopyBtn text={data.vless_url} />
                </div>
                <div className="ma-link-hint">Для роутеров (OpenWrt + Passwall2)</div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══ Setup Instructions ═══ */}
      <div className="ma-card">
        <div className="ma-card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
            <line x1="12" y1="18" x2="12.01" y2="18" />
          </svg>
          Настройка по платформам
        </div>

        <div className="ma-platforms">
          {platformMeta.map(p => (
            <button
              key={p.id}
              className={`ma-platform-chip ${platform === p.id ? 'active' : ''}`}
              onClick={() => setPlatform(platform === p.id ? null : p.id)}
            >
              <span className="ma-plat-icon">{p.icon}</span>
              <span>{p.label}</span>
            </button>
          ))}
        </div>

        {platform === 'ios' && (
          <div className="ma-instructions" key="ios">
            <div className="ma-inst-app">
              <span>V2RayTun</span>
              <a href="https://apps.apple.com/app/v2raytun/id6476628951" target="_blank" rel="noopener" className="ma-inst-link">
                {externalLinkIcon} App Store
              </a>
            </div>
            <ol className="ma-steps">
              <li>Установите <strong>V2RayTun</strong> из App Store</li>
              <li>Нажмите <strong>«Импорт подписки»</strong> выше — откроется приложение</li>
              <li>Нажмите <strong>«Импорт маршрутов»</strong> — добавятся правила маршрутизации</li>
              <li>Включите VPN — нажмите <strong>▶️</strong> и разрешите VPN-профиль</li>
            </ol>
            <div className="ma-inst-note">💡 Если deeplink не работает — скопируйте URL подписки и вставьте вручную: V2RayTun → ☰ → Подписка → +</div>
          </div>
        )}

        {platform === 'android' && (
          <div className="ma-instructions" key="android">
            <div className="ma-inst-app">
              <span>v2rayNG</span>
              <a href="https://play.google.com/store/apps/details?id=com.v2ray.ang" target="_blank" rel="noopener" className="ma-inst-link">
                {externalLinkIcon} Google Play
              </a>
            </div>
            <ol className="ma-steps">
              <li>Установите <strong>v2rayNG</strong> из Google Play</li>
              <li>Скопируйте URL подписки из раздела выше</li>
              <li>v2rayNG → ☰ → <strong>Подписка → +</strong> → вставьте URL</li>
              <li>Потяните список вниз для обновления, нажмите <strong>▶️</strong></li>
            </ol>
          </div>
        )}

        {platform === 'windows' && (
          <div className="ma-instructions" key="windows">
            <div className="ma-inst-app">
              <span>v2rayN</span>
              <a href="https://github.com/2dust/v2rayN/releases" target="_blank" rel="noopener" className="ma-inst-link">
                {externalLinkIcon} GitHub
              </a>
            </div>
            <ol className="ma-steps">
              <li>Скачайте <strong>v2rayN</strong> с GitHub Releases, распакуйте</li>
              <li>Скопируйте URL подписки из раздела выше</li>
              <li>v2rayN → Subscription → Add → вставьте URL</li>
              <li>Update → выберите сервер → Enable System Proxy</li>
            </ol>
          </div>
        )}

        {platform === 'macos' && (
          <div className="ma-instructions" key="macos">
            <div className="ma-inst-app">
              <span>V2RayTun</span>
              <a href="https://apps.apple.com/app/v2raytun/id6476628951" target="_blank" rel="noopener" className="ma-inst-link">
                {externalLinkIcon} App Store
              </a>
            </div>
            <ol className="ma-steps">
              <li>Установите <strong>V2RayTun</strong> из App Store</li>
              <li>Нажмите кнопку «Импорт подписки» выше, или скопируйте URL</li>
              <li>V2RayTun → Подписка → + → вставьте URL</li>
              <li>Нажмите кнопку подключения и разрешите VPN-профиль</li>
            </ol>
          </div>
        )}

        {platform === 'router' && (
          <div className="ma-instructions" key="router">
            <div className="ma-inst-app">
              <span>OpenWrt + Passwall2</span>
            </div>
            <ol className="ma-steps">
              <li>Убедитесь, что на роутере установлен <strong>OpenWrt</strong></li>
              <li>Установите <strong>Passwall2</strong> через opkg</li>
              <li>Скопируйте прямую VLESS-ссылку из раздела выше</li>
              <li>Passwall2 → Servers → Import URL → вставьте ссылку</li>
            </ol>
          </div>
        )}
      </div>

      {/* ═══ FAQ ═══ */}
      <div className="ma-card">
        <div className="ma-card-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          Частые вопросы
        </div>

        <div className="ma-faq">
          <details className="ma-faq-item">
            <summary>Не работает VPN — что делать?</summary>
            <p>1. Проверьте интернет без VPN<br/>2. Обновите подписку в приложении<br/>3. Попробуйте переподключиться<br/>4. Создайте тикет в разделе «Тикеты»</p>
          </details>
          <details className="ma-faq-item">
            <summary>Как обновить конфигурацию?</summary>
            <p>Подписка обновляется автоматически. Для ручного обновления: потяните список серверов вниз (Android) или нажмите «Обновить» в настройках подписки (iOS).</p>
          </details>
          <details className="ma-faq-item">
            <summary>Какие сайты идут через VPN?</summary>
            <p>Через VPN: YouTube, Instagram, TikTok, Discord, Telegram, ChatGPT и другие заблокированные сервисы.<br/>Напрямую: VK, Яндекс, Сбер, Авито и другие российские сайты.</p>
          </details>
          <details className="ma-faq-item">
            <summary>Закончился трафик?</summary>
            <p>Создайте тикет в разделе «Тикеты» для сброса или увеличения лимита.</p>
          </details>
        </div>
      </div>
    </div>
  );
}
