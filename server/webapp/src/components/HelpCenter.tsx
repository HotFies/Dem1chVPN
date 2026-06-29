import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Apple,
  Smartphone,
  Monitor,
  Laptop,
  Router,
  Link as LinkIcon,
  Network as NetworkIcon,
  HelpCircle,
  ExternalLink,
  ArrowRight,
  Globe,
  LifeBuoy,
  LucideIcon,
} from 'lucide-react'
import { getMyLinks, type MyLinks } from '../api/client'
import { CopyButton } from './ui/CopyButton'
import { Button } from './ui/Button'
import { Skeleton, SkeletonStack } from './ui/Skeleton'
import { useToast } from '../hooks/useToast'

type Platform = 'ios' | 'android' | 'windows' | 'macos' | 'router' | null

const PLATFORMS: { id: Exclude<Platform, null>; icon: LucideIcon; label: string }[] = [
  { id: 'ios', icon: Apple, label: 'iOS' },
  { id: 'android', icon: Smartphone, label: 'Android' },
  { id: 'windows', icon: Monitor, label: 'Windows' },
  { id: 'macos', icon: Laptop, label: 'macOS' },
  { id: 'router', icon: Router, label: 'Роутер' },
]

function openDeeplink(redirectUrl: string | null | undefined, fallbackDeeplink: string) {
  const tg = (window as any).Telegram?.WebApp
  if (redirectUrl && tg?.openLink) tg.openLink(redirectUrl)
  else if (redirectUrl) window.open(redirectUrl, '_blank')
  else window.location.href = fallbackDeeplink
}

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } },
}
const childItem = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 260, damping: 24 } },
}

function Step({ n, title, children }: { n: number; title: React.ReactNode; children?: React.ReactNode }) {
  return (
    <li className="help-step">
      <div className="step-number">{n}</div>
      <div className="step-content">
        <strong>{title}</strong>
        {children && <div className="step-body">{children}</div>}
      </div>
    </li>
  )
}

export default function HelpCenter({ onOpenGuide }: { onOpenGuide?: () => void }) {
  const [links, setLinks] = useState<MyLinks | null>(null)
  const [loading, setLoading] = useState(true)
  const [platform, setPlatform] = useState<Platform>(null)
  const toast = useToast()

  useEffect(() => {
    getMyLinks()
      .then(setLinks)
      .catch(() => setLinks(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="help-center">
        <div className="ma-card"><Skeleton height={64} radius="lg" /></div>
        <div className="ma-card"><SkeletonStack rows={3} height={36} /></div>
      </div>
    )
  }

  const launchSub = () => {
    if (!links?.sub_deeplink) return
    openDeeplink(links.sub_redirect_url, links.sub_deeplink)
    toast.info('Открываю V2RayTun…')
  }
  const launchRoute = () => {
    if (!links?.route_deeplink) return
    openDeeplink(links.route_redirect_url, links.route_deeplink)
    toast.info('Открываю импорт маршрутов…')
  }

  return (
    <motion.div className="help-center" variants={stagger} initial="hidden" animate="show">
      <div className="section-header">
        <div className="section-icon">
          <LifeBuoy size={22} strokeWidth={1.75} />
        </div>
        <h2>Помощь и инструкции</h2>
      </div>

      {/* Ссылки пользователя */}
      {links?.has_account && (
        <motion.div variants={childItem} className="card help-links-card">
          <div className="card-header">
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <LinkIcon size={18} strokeWidth={1.75} color="var(--accent)" />
              Ваши ссылки — {links.name}
            </span>
          </div>
          <div className="card-body">
            {links.sub_url && (
              <div className="link-section">
                <span className="link-label">
                  <NetworkIcon size={13} strokeWidth={2} /> Подписка (автообновление)
                </span>
                <div className="link-row">
                  <div className="link-value">{links.sub_url}</div>
                  <CopyButton text={links.sub_url} />
                </div>
              </div>
            )}
            {links.sub_deeplink && (
              <div className="link-section">
                <span className="link-label">
                  <Apple size={13} strokeWidth={2} /> v2RayTun — iOS автоимпорт
                </span>
                <div className="link-row">
                  <div className="link-value">{links.sub_deeplink}</div>
                  <CopyButton text={links.sub_deeplink} />
                </div>
                <Button variant="subtle" size="sm" fullWidth onClick={launchSub} leftIcon={<ArrowRight size={14} />}>
                  Открыть в V2RayTun
                </Button>
              </div>
            )}
            {links.route_deeplink && (
              <div className="link-section">
                <span className="link-label">
                  <NetworkIcon size={13} strokeWidth={2} /> Маршрутизация — iOS
                </span>
                <div className="link-row">
                  <div className="link-value" style={{ maxHeight: 60, overflow: 'hidden' }}>
                    {links.route_deeplink}
                  </div>
                  <CopyButton text={links.route_deeplink} />
                </div>
                <Button variant="ghost" size="sm" fullWidth onClick={launchRoute} leftIcon={<ArrowRight size={14} />}>
                  Импорт маршрутов
                </Button>
              </div>
            )}
            {links.vless_url && (
              <div className="link-section">
                <span className="link-label">
                  <LinkIcon size={13} strokeWidth={2} /> Прямая VLESS ссылка
                </span>
                <div className="link-row">
                  <div className="link-value" style={{ maxHeight: 60, overflow: 'hidden' }}>
                    {links.vless_url}
                  </div>
                  <CopyButton text={links.vless_url} />
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Платформы */}
      <motion.div variants={childItem} className="card">
        <div className="card-header">
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Smartphone size={18} strokeWidth={1.75} color="var(--accent)" />
            Выберите платформу
          </span>
        </div>
        <div className="card-body">
          <div className="help-platforms">
            {PLATFORMS.map(p => {
              const Ico = p.icon
              const active = platform === p.id
              return (
                <button
                  key={p.id}
                  type="button"
                  className={`help-platform-btn ${active ? 'active' : ''}`}
                  onClick={() => setPlatform(active ? null : p.id)}
                >
                  <Ico size={18} strokeWidth={1.75} />
                  <span>{p.label}</span>
                </button>
              )
            })}
          </div>
        </div>
      </motion.div>

      <AnimatePresence mode="wait">
        {platform === 'ios' && (
          <motion.div
            key="ios" className="card help-instructions"
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
          >
            <div className="card-header"><span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Apple size={18} strokeWidth={1.75} color="var(--accent)" /> Инструкция для iOS</span></div>
            <div className="card-body">
              <button type="button" className="guide-banner" onClick={onOpenGuide}>
                <div className="guide-banner-icon"><Globe size={22} /></div>
                <div className="guide-banner-text">
                  <strong>Приложение удалено из App Store РФ?</strong>
                  <span>Нажмите, чтобы открыть инструкцию по смене региона</span>
                </div>
                <ArrowRight size={20} strokeWidth={2.5} className="guide-banner-arrow" />
              </button>

              <div className="help-app-header">
                <span className="help-app-name">V2RayTun</span>
                <a href="https://apps.apple.com/app/v2raytun/id6476628951" target="_blank" rel="noopener" className="help-download-btn">
                  <ExternalLink size={13} /> App Store
                </a>
              </div>

              <ol className="help-steps">
                <Step n={1} title="Установите V2RayTun">Скачайте из App Store по ссылке выше</Step>
                <Step n={2} title="Импорт подписки">
                  Скопируйте ссылку <code>v2raytun://import/...</code> из блока «Ваши ссылки».<br />
                  Откройте её в <b>Safari</b> — подписка добавится автоматически
                </Step>
                <Step n={3} title="Импорт маршрутизации">
                  Скопируйте ссылку <code>v2raytun://import_route/...</code>.<br />
                  Откройте её в <b>Safari</b> — правила маршрутизации добавятся
                </Step>
                <Step n={4} title="Подключитесь">
                  Нажмите кнопку запуска в приложении и разрешите установку VPN-профиля
                </Step>
              </ol>

              <div className="help-note">
                Если deeplink не работает — вставьте URL подписки вручную: V2RayTun → ☰ → Подписка → + → URL
              </div>
            </div>
          </motion.div>
        )}

        {platform === 'android' && (
          <motion.div
            key="android" className="card help-instructions"
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
          >
            <div className="card-header"><span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Smartphone size={18} strokeWidth={1.75} color="var(--accent)" /> Инструкция для Android</span></div>
            <div className="card-body">
              <div className="help-app-header">
                <span className="help-app-name">v2rayNG</span>
                <a href="https://play.google.com/store/apps/details?id=com.v2ray.ang" target="_blank" rel="noopener" className="help-download-btn">
                  <ExternalLink size={13} /> Google Play
                </a>
              </div>
              <ol className="help-steps">
                <Step n={1} title="Установите v2rayNG">Скачайте из Google Play</Step>
                <Step n={2} title="Добавьте подписку">
                  Скопируйте URL подписки из блока «Ваши ссылки».<br />
                  v2rayNG → ☰ → Подписка → + → Вставьте URL
                </Step>
                <Step n={3} title="Обновите подписку">Потяните список вниз для обновления</Step>
                <Step n={4} title="Подключитесь">Нажмите кнопку подключения внизу экрана</Step>
              </ol>
            </div>
          </motion.div>
        )}

        {platform === 'windows' && (
          <motion.div
            key="windows" className="card help-instructions"
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
          >
            <div className="card-header"><span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Monitor size={18} strokeWidth={1.75} color="var(--accent)" /> Инструкция для Windows</span></div>
            <div className="card-body">
              <div className="help-app-header">
                <span className="help-app-name">Dem1chVPN</span>
                <a
                  href="https://github.com/HotFies/Dem1chVPN/releases/latest"
                  target="_blank" rel="noopener" className="help-download-btn"
                >
                  <ExternalLink size={13} /> Скачать
                </a>
              </div>
              <ol className="help-steps">
                <Step n={1} title="Скачайте Dem1chVPN">Загрузите Dem1chVPN-Setup.exe по кнопке выше</Step>
                <Step n={2} title="Установите приложение">Запустите установщик и следуйте инструкциям</Step>
                <Step n={3} title="Импортируйте подписку">
                  Нажмите «Импорт подписки» (Windows) в разделе «Ваши ссылки».<br />
                  Или скопируйте URL подписки и вставьте в настройках приложения
                </Step>
                <Step n={4} title="Подключитесь">Нажмите кнопку подключения — готово</Step>
              </ol>
              <div className="help-note">
                Альтернатива: <a href="https://github.com/2dust/v2rayN/releases" target="_blank" rel="noopener">v2rayN</a> — Subscription → Add → вставьте URL подписки
              </div>
            </div>
          </motion.div>
        )}

        {platform === 'macos' && (
          <motion.div
            key="macos" className="card help-instructions"
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
          >
            <div className="card-header"><span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Laptop size={18} strokeWidth={1.75} color="var(--accent)" /> Инструкция для macOS</span></div>
            <div className="card-body">
              <div className="help-app-header">
                <span className="help-app-name">V2RayTun</span>
                <a href="https://apps.apple.com/app/v2raytun/id6476628951" target="_blank" rel="noopener" className="help-download-btn">
                  <ExternalLink size={13} /> App Store
                </a>
              </div>
              <ol className="help-steps">
                <Step n={1} title="Установите V2RayTun из App Store" />
                <Step n={2} title="Добавьте подписку">
                  Откройте deeplink <code>v2raytun://import/...</code> в Safari.<br />
                  Или: V2RayTun → Подписка → + → Вставьте URL
                </Step>
                <Step n={3} title="Подключитесь">Нажмите кнопку подключения и разрешите VPN-профиль</Step>
              </ol>
            </div>
          </motion.div>
        )}

        {platform === 'router' && (
          <motion.div
            key="router" className="card help-instructions"
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
            transition={{ type: 'spring', stiffness: 320, damping: 28 }}
          >
            <div className="card-header"><span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Router size={18} strokeWidth={1.75} color="var(--accent)" /> Инструкция для роутера</span></div>
            <div className="card-body">
              <div className="help-app-header"><span className="help-app-name">OpenWrt + Passwall2</span></div>
              <ol className="help-steps">
                <Step n={1} title="Установите прошивку OpenWrt" />
                <Step n={2} title="Установите Passwall2">Через opkg или из репозитория Passwall</Step>
                <Step n={3} title="Добавьте сервер">
                  Скопируйте прямую VLESS-ссылку.<br />
                  Passwall2 → Servers → Import URL → Вставьте
                </Step>
                <Step n={4} title="Настройте маршрутизацию">
                  Укажите URL подписки (Direct domains):
                  {links?.sub_url && (
                    <div className="link-row" style={{ marginTop: 8 }}>
                      <div className="link-value" style={{ fontSize: 10 }}>
                        {links.sub_url}/direct
                      </div>
                      <CopyButton text={`${links.sub_url}/direct`} />
                    </div>
                  )}
                </Step>
              </ol>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!platform && (
        <motion.div variants={childItem} className="card">
          <div className="card-header">
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <HelpCircle size={18} strokeWidth={1.75} color="var(--warning)" />
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
                <p>Через VPN обычно идут заблокированные в вашем регионе сервисы (YouTube, Instagram, TikTok, Discord, ChatGPT и др.), а российские сайты (VK, Яндекс, Сбер, Авито) — напрямую.<br/>
                   Точный список зависит от правил маршрутизации вашей подписки и может настраиваться администратором.</p>
              </details>
              <details className="faq-item">
                <summary>Закончился трафик — что делать?</summary>
                <p>Обратитесь к администратору для сброса трафика или увеличения лимита. Создайте тикет в разделе «Тикеты».</p>
              </details>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
