import React, { useState, useEffect } from 'react';
import { getMyLinks, type MyLinks } from '../api/client';

type Platform = 'ios' | 'android' | 'windows' | 'macos' | 'router' | null;

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

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      className={`btn-copy ${copied ? 'copied' : ''}`}
      onClick={copy}
      title={copied ? 'Скопировано!' : 'Копировать'}
    >
      {copied ? checkIcon : copyIcon}
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

export default function HelpCenter({ onOpenGuide }: { onOpenGuide?: () => void }) {
  const [links, setLinks] = useState<MyLinks | null>(null);
  const [loading, setLoading] = useState(true);
  const [platform, setPlatform] = useState<Platform>(null);

  useEffect(() => {
    getMyLinks()
      .then(setLinks)
      .catch(() => setLinks(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="help-center">
        <div className="loading-page">
          <div className="spinner" />
          <span>Загрузка...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="help-center">
      <div className="section-header">
        <h2>
          <span className="section-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          </span>
          Помощь и инструкции
        </h2>
      </div>

      {/* Personal Links Card */}
      {links?.has_account && (
        <div className="card help-links-card">
          <div className="card-header">
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
              </svg>
              Ваши ссылки — {links.name}
            </span>
          </div>
          <div className="card-body">
            {links.sub_url && (
              <div className="link-section">
                <span className="link-label">📡 Подписка (автообновление)</span>
                <div className="link-row">
                  <div className="link-value">{links.sub_url}</div>
                  <CopyButton text={links.sub_url} />
                </div>
              </div>
            )}
            {links.sub_deeplink && (
              <div className="link-section">
                <span className="link-label">📱 v2RayTun — iOS автоимпорт</span>
                <div className="link-row">
                  <div className="link-value">{links.sub_deeplink}</div>
                  <CopyButton text={links.sub_deeplink} />
                </div>
                <button className="btn-open-deeplink" onClick={() => openDeeplink(links.sub_deeplink!)}>
                  Открыть в V2RayTun
                </button>
              </div>
            )}
            {links.route_deeplink && (
              <div className="link-section">
                <span className="link-label">🔀 Маршрутизация — iOS</span>
                <div className="link-row">
                  <div className="link-value" style={{ maxHeight: 60, overflow: 'hidden' }}>
                    {links.route_deeplink.substring(0, 80)}...
                  </div>
                  <CopyButton text={links.route_deeplink} />
                </div>
                <button className="btn-open-deeplink" onClick={() => openDeeplink(links.route_deeplink!)}>
                  Импорт маршрутов
                </button>
              </div>
            )}
            {links.vless_url && (
              <div className="link-section">
                <span className="link-label">🔗 Прямая VLESS ссылка</span>
                <div className="link-row">
                  <div className="link-value" style={{ maxHeight: 60, overflow: 'hidden' }}>
                    {links.vless_url.substring(0, 80)}...
                  </div>
                  <CopyButton text={links.vless_url} />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Platform Selection */}
      <div className="card">
        <div className="card-header">
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
              <line x1="12" y1="18" x2="12.01" y2="18" />
            </svg>
            Выберите платформу
          </span>
        </div>
        <div className="card-body">
          <div className="help-platforms">
            {([
              { id: 'ios' as Platform, icon: '🍎', label: 'iOS' },
              { id: 'android' as Platform, icon: '🤖', label: 'Android' },
              { id: 'windows' as Platform, icon: '🖥️', label: 'Windows' },
              { id: 'macos' as Platform, icon: '🍏', label: 'macOS' },
              { id: 'router' as Platform, icon: '📡', label: 'Роутер' },
            ]).map(p => (
              <button
                key={p.id}
                className={`help-platform-btn ${platform === p.id ? 'active' : ''}`}
                onClick={() => setPlatform(platform === p.id ? null : p.id)}
              >
                <span className="platform-icon">{p.icon}</span>
                <span>{p.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Platform Instructions */}
      {platform === 'ios' && (
        <div className="card help-instructions" key="ios">
          <div className="card-header">
            <span>🍎 Инструкция для iOS</span>
          </div>
          <div className="card-body">
            {/* Region change banner */}
            <div className="guide-banner" onClick={onOpenGuide}>
              <div className="guide-banner-icon">🇺🇸</div>
              <div className="guide-banner-text">
                <strong>Приложение удалено из App Store РФ?</strong>
                <span>Нажмите, чтобы открыть инструкцию по смене региона</span>
              </div>
              <svg className="guide-banner-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </div>

            <div className="help-app-header">
              <span className="help-app-name">V2RayTun</span>
              <a href="https://apps.apple.com/app/v2raytun/id6476628951" target="_blank" rel="noopener" className="help-download-btn">
                📥 App Store
              </a>
            </div>

            <div className="help-steps">
              <div className="help-step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <strong>Установите V2RayTun</strong>
                  <p>Скачайте из App Store по ссылке выше</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <strong>Импорт подписки</strong>
                  <p>Скопируйте ссылку <code>v2raytun://import/...</code> из блока «Ваши ссылки» выше</p>
                  <p>Откройте её в <b>Safari</b> — подписка добавится автоматически</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">3</div>
                <div className="step-content">
                  <strong>Импорт маршрутизации</strong>
                  <p>Скопируйте ссылку <code>v2raytun://import_route/...</code></p>
                  <p>Откройте её в <b>Safari</b> — правила маршрутизации добавятся</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">4</div>
                <div className="step-content">
                  <strong>Подключитесь</strong>
                  <p>Нажмите кнопку ▶️ в приложении</p>
                  <p>Разрешите установку VPN-профиля</p>
                </div>
              </div>
            </div>

            <div className="help-note">
              💡 Если deeplink не работает — вставьте URL подписки вручную: V2RayTun → ☰ → Подписка → + → Вставьте URL
            </div>
          </div>
        </div>
      )}

      {platform === 'android' && (
        <div className="card help-instructions" key="android">
          <div className="card-header">
            <span>🤖 Инструкция для Android</span>
          </div>
          <div className="card-body">
            <div className="help-app-header">
              <span className="help-app-name">v2rayNG</span>
              <a href="https://play.google.com/store/apps/details?id=com.v2ray.ang" target="_blank" rel="noopener" className="help-download-btn">
                📥 Google Play
              </a>
            </div>

            <div className="help-steps">
              <div className="help-step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <strong>Установите v2rayNG</strong>
                  <p>Скачайте из Google Play</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <strong>Добавьте подписку</strong>
                  <p>Скопируйте URL подписки из блока «Ваши ссылки»</p>
                  <p>v2rayNG → ☰ → Подписка → + → Вставьте URL</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">3</div>
                <div className="step-content">
                  <strong>Обновите подписку</strong>
                  <p>Потяните список вниз для обновления</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">4</div>
                <div className="step-content">
                  <strong>Подключитесь</strong>
                  <p>Нажмите кнопку ▶️ внизу экрана</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {platform === 'windows' && (
        <div className="card help-instructions" key="windows">
          <div className="card-header">
            <span>🖥️ Инструкция для Windows</span>
          </div>
          <div className="card-body">
            <div className="help-app-header">
              <span className="help-app-name">v2rayN</span>
              <a href="https://github.com/2dust/v2rayN/releases" target="_blank" rel="noopener" className="help-download-btn">
                📥 GitHub
              </a>
            </div>

            <div className="help-steps">
              <div className="help-step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <strong>Скачайте v2rayN</strong>
                  <p>Загрузите последнюю версию с GitHub Releases</p>
                  <p>Распакуйте архив в удобную папку</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <strong>Добавьте подписку</strong>
                  <p>Скопируйте URL подписки из блока выше</p>
                  <p>v2rayN → Subscription → Add → Вставьте URL</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">3</div>
                <div className="step-content">
                  <strong>Обновите и подключитесь</strong>
                  <p>Subscription → Update → Выберите сервер</p>
                  <p>Правый клик на иконку в трее → System Proxy → Enable</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {platform === 'macos' && (
        <div className="card help-instructions" key="macos">
          <div className="card-header">
            <span>🍏 Инструкция для macOS</span>
          </div>
          <div className="card-body">
            <div className="help-app-header">
              <span className="help-app-name">V2RayTun</span>
              <a href="https://apps.apple.com/app/v2raytun/id6476628951" target="_blank" rel="noopener" className="help-download-btn">
                📥 App Store
              </a>
            </div>

            <div className="help-steps">
              <div className="help-step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <strong>Установите V2RayTun из App Store</strong>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <strong>Добавьте подписку</strong>
                  <p>Откройте deeplink <code>v2raytun://import/...</code> в Safari, или</p>
                  <p>V2RayTun → Подписка → + → Вставьте URL подписки</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">3</div>
                <div className="step-content">
                  <strong>Подключитесь</strong>
                  <p>Нажмите кнопку подключения и разрешите VPN-профиль</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {platform === 'router' && (
        <div className="card help-instructions" key="router">
          <div className="card-header">
            <span>📡 Инструкция для роутера</span>
          </div>
          <div className="card-body">
            <div className="help-app-header">
              <span className="help-app-name">OpenWrt + Passwall2</span>
            </div>

            <div className="help-steps">
              <div className="help-step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <strong>Установите прошивку OpenWrt</strong>
                  <p>Убедитесь, что на роутере стоит OpenWrt</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <strong>Установите Passwall2</strong>
                  <p>Через opkg или из репозитория Passwall</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">3</div>
                <div className="step-content">
                  <strong>Добавьте сервер</strong>
                  <p>Скопируйте прямую VLESS-ссылку</p>
                  <p>Passwall2 → Servers → Import URL → Вставьте</p>
                </div>
              </div>

              <div className="help-step">
                <div className="step-number">4</div>
                <div className="step-content">
                  <strong>Настройте маршрутизацию</strong>
                  <p>Укажите URL подписки (Direct domains):</p>
                  {links?.sub_url && (
                    <div className="link-row" style={{ marginTop: 8 }}>
                      <div className="link-value" style={{ fontSize: 10 }}>
                        {links.sub_url}/direct
                      </div>
                      <CopyButton text={`${links.sub_url}/direct`} />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* FAQ */}
      {!platform && (
        <div className="card">
          <div className="card-header">
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01" />
                <circle cx="12" cy="12" r="10" />
              </svg>
              Частые вопросы
            </span>
          </div>
          <div className="card-body">
            <div className="help-faq">
              <details className="faq-item">
                <summary>Не работает VPN — что делать?</summary>
                <p>1. Проверьте подключение к интернету без VPN<br/>
                   2. Обновите подписку в приложении<br/>
                   3. Попробуйте переподключиться<br/>
                   4. Создайте тикет в разделе «Тикеты»</p>
              </details>
              <details className="faq-item">
                <summary>Как обновить конфигурацию?</summary>
                <p>Подписка обновляется автоматически каждые 6 часов. Для ручного обновления: потяните список серверов вниз (Android) или нажмите «Обновить» в настройках подписки.</p>
              </details>
              <details className="faq-item">
                <summary>Какие сайты идут через VPN?</summary>
                <p>Через VPN: YouTube, Instagram, TikTok, Discord, Telegram, ChatGPT и другие заблокированные сервисы.<br/>
                   Напрямую: VK, Яндекс, Сбер, Авито и другие российские сайты (для скорости).</p>
              </details>
              <details className="faq-item">
                <summary>Закончился трафик — что делать?</summary>
                <p>Обратитесь к администратору для сброса трафика или увеличения лимита. Создайте тикет в разделе «Тикеты».</p>
              </details>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
