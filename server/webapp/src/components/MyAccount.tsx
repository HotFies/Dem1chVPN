import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Apple,
  Smartphone,
  Monitor,
  Laptop,
  Router,
  Link as LinkIcon,
  Download,
  Network as NetworkIcon,
  ShieldCheck,
  Clock,
  ArrowUp,
  ArrowDown,
  Infinity as InfinityIcon,
  HelpCircle,
  ChevronDown,
  Activity,
  User,
  ExternalLink,
  LucideIcon,
} from 'lucide-react'
import { getMyAccount, formatBytes, type MyAccount as MyAccountData } from '../api/client'
import { CopyButton } from './ui/CopyButton'
import { Button } from './ui/Button'
import { StatusPill } from './ui/StatusPill'
import { Skeleton, SkeletonStack } from './ui/Skeleton'
import { useToast } from '../hooks/useToast'

function openDeeplink(redirectUrl: string | null | undefined, fallbackDeeplink: string) {
  const tg = (window as any).Telegram?.WebApp
  if (redirectUrl && tg?.openLink) tg.openLink(redirectUrl)
  else if (redirectUrl) window.open(redirectUrl, '_blank')
  else window.location.href = fallbackDeeplink
}

type Platform = 'ios' | 'android' | 'windows' | 'macos' | 'router' | null

const PLATFORMS: { id: Exclude<Platform, null>; icon: LucideIcon; label: string }[] = [
  { id: 'ios', icon: Apple, label: 'iOS' },
  { id: 'android', icon: Smartphone, label: 'Android' },
  { id: 'windows', icon: Monitor, label: 'Windows' },
  { id: 'macos', icon: Laptop, label: 'macOS' },
  { id: 'router', icon: Router, label: 'Роутер' },
]

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return 'Бессрочно'
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function daysLeft(iso: string | null | undefined): string {
  if (!iso) return ''
  const diff = Math.ceil((new Date(iso).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  if (diff < 0) return 'истёк'
  if (diff === 0) return 'сегодня'
  const m10 = diff % 10
  const m100 = diff % 100
  const word = (m10 === 1 && m100 !== 11) ? 'день'
    : (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) ? 'дня'
    : 'дней'
  return `${diff} ${word}`
}

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.04 } },
}
const childItem = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 260, damping: 24 } },
}

export default function MyAccount() {
  const [data, setData] = useState<MyAccountData | null>(null)
  const [loading, setLoading] = useState(true)
  const [platform, setPlatform] = useState<Platform>(null)
  const [linksOpen, setLinksOpen] = useState(true)
  const toast = useToast()

  useEffect(() => {
    getMyAccount()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="my-account">
        <div className="ma-card" style={{ padding: 18 }}>
          <Skeleton height={68} radius="lg" />
          <div style={{ height: 12 }} />
          <Skeleton height={18} width="50%" />
        </div>
        <div className="ma-card" style={{ padding: 18 }}>
          <SkeletonStack rows={4} height={14} />
        </div>
        <div className="ma-card" style={{ padding: 18 }}>
          <SkeletonStack rows={3} height={42} />
        </div>
      </div>
    )
  }

  if (!data?.has_account) {
    return (
      <div className="my-account">
        <div className="ma-no-account">
          <div className="ma-no-account-icon">
            <ShieldCheck size={40} strokeWidth={1.5} />
          </div>
          <h3>Нет VPN-аккаунта</h3>
          <p>Обратитесь к администратору для получения доступа.</p>
        </div>
      </div>
    )
  }

  const trafficPct = data.traffic_percent ?? 0
  const isLimited = data.traffic_limit != null && data.traffic_limit > 0
  const isExpired = data.expired
  const isActive = data.active && !isExpired

  const barColor = trafficPct > 90 ? 'var(--danger)' : trafficPct > 70 ? 'var(--warning)' : 'var(--accent)'

  const launchSubscription = () => {
    if (!data.sub_deeplink) return
    openDeeplink(data.sub_redirect_url, data.sub_deeplink)
    toast.info('Открываю V2RayTun…')
  }

  const launchRouting = () => {
    if (!data.route_deeplink) return
    openDeeplink(data.route_redirect_url, data.route_deeplink)
    toast.info('Открываю импорт маршрутов…')
  }

  const launchWindows = () => {
    if (!data.win_sub_deeplink) return
    openDeeplink(data.win_sub_redirect_url, data.win_sub_deeplink)
    toast.info('Открываю Dem1chVPN…')
  }

  return (
    <motion.div className="my-account" variants={stagger} initial="hidden" animate="show">
      {/* HERO */}
      <motion.div
        variants={childItem}
        className={`ma-hero ${isActive ? 'ma-hero--active' : 'ma-hero--inactive'}`}
      >
        <div className="ma-hero-top">
          <div className="ma-hero-user">
            <div className={`ma-avatar ${isActive ? 'active' : 'inactive'}`}>
              <User size={20} strokeWidth={1.75} />
            </div>
            <div>
              <div className="ma-user-name">{data.name}</div>
              <div className="ma-user-since">с {fmtDate(data.created)}</div>
            </div>
          </div>
          <StatusPill tone={isActive ? 'active' : isExpired ? 'expired' : 'inactive'}>
            {isActive ? 'Активен' : isExpired ? 'Истёк' : 'Заблокирован'}
          </StatusPill>
        </div>

        {data.expiry && (
          <div className="ma-expiry-row">
            <Clock size={14} strokeWidth={2} />
            <span>
              {isExpired
                ? <>Срок истёк {fmtDate(data.expiry)}</>
                : <>Действует до <strong>{fmtDate(data.expiry)}</strong> <span className="ma-days-left">({daysLeft(data.expiry)})</span></>}
            </span>
          </div>
        )}
      </motion.div>

      {/* TRAFFIC */}
      <motion.div variants={childItem} className="ma-card">
        <div className="ma-card-title">
          <Activity size={18} strokeWidth={1.75} />
          Трафик
        </div>

        <div className="ma-traffic-grid">
          <div className="ma-traffic-cell upload">
            <span className="ma-traffic-dir">
              <ArrowUp size={12} strokeWidth={2.5} /> Upload
            </span>
            <span className="ma-traffic-val num">{formatBytes(data.traffic_up ?? 0)}</span>
          </div>
          <div className="ma-traffic-cell download">
            <span className="ma-traffic-dir">
              <ArrowDown size={12} strokeWidth={2.5} /> Download
            </span>
            <span className="ma-traffic-val num">{formatBytes(data.traffic_down ?? 0)}</span>
          </div>
        </div>

        {isLimited ? (
          <div className="ma-progress-wrap">
            <div className="ma-progress-info">
              <span>Использовано</span>
              <span className="ma-progress-nums num">
                {formatBytes(data.traffic_total ?? 0)} / {formatBytes(data.traffic_limit!)}
              </span>
            </div>
            <div className="ma-progress-bar">
              <motion.div
                className="ma-progress-fill"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: Math.min(trafficPct / 100, 1) }}
                transition={{ type: 'spring', stiffness: 110, damping: 22, delay: 0.15 }}
                style={{
                  background: `linear-gradient(90deg, ${barColor}, color-mix(in srgb, ${barColor} 80%, white))`,
                  transformOrigin: 'left center',
                }}
              />
            </div>
            <div className="ma-progress-pct num" style={{ color: barColor }}>{trafficPct}%</div>
          </div>
        ) : (
          <div className="ma-unlimited-badge">
            <InfinityIcon size={14} strokeWidth={2} />
            Безлимитный трафик
          </div>
        )}
      </motion.div>

      {/* LINKS */}
      <motion.div variants={childItem} className="ma-card">
        <button
          type="button"
          className="ma-card-toggle"
          onClick={() => setLinksOpen(v => !v)}
          aria-expanded={linksOpen}
        >
          <div className="ma-card-title" style={{ marginBottom: 0 }}>
            <LinkIcon size={18} strokeWidth={1.75} />
            Подключение и ссылки
          </div>
          <motion.span animate={{ rotate: linksOpen ? 180 : 0 }} transition={{ type: 'spring', stiffness: 280, damping: 22 }} className="ma-chevron-wrap">
            <ChevronDown size={18} strokeWidth={2} />
          </motion.span>
        </button>

        <AnimatePresence initial={false}>
          {linksOpen && (
            <motion.div
              key="links"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 260, damping: 28 }}
              style={{ overflow: 'hidden' }}
            >
              <div className="ma-links-body">
                {data.sub_url && (
                  <div className="ma-link-block">
                    <div className="ma-link-label">
                      <NetworkIcon size={14} strokeWidth={2} />
                      Подписка (автообновление)
                    </div>
                    <div className="ma-link-row">
                      <code className="ma-link-value">{data.sub_url}</code>
                      <CopyButton text={data.sub_url} />
                    </div>
                    <div className="ma-link-hint">v2rayN · v2rayNG · Streisand · V2Box</div>
                  </div>
                )}

                {data.sub_deeplink && (
                  <div className="ma-link-block ma-ios-block">
                    <div className="ma-link-label">
                      <Apple size={14} strokeWidth={2} />
                      iOS — V2RayTun (быстрый импорт)
                    </div>
                    <Button variant="subtle" size="md" fullWidth leftIcon={<Download size={16} />} onClick={launchSubscription}>
                      Импорт подписки
                    </Button>
                    <div className="ma-link-row ma-link-row--compact">
                      <code className="ma-link-value ma-link-value--small">{data.sub_deeplink}</code>
                      <CopyButton text={data.sub_deeplink} />
                    </div>
                  </div>
                )}

                {data.route_deeplink && (
                  <div className="ma-link-block">
                    <div className="ma-link-label">
                      <NetworkIcon size={14} strokeWidth={2} />
                      Маршрутизация — iOS
                    </div>
                    <Button variant="ghost" size="md" fullWidth leftIcon={<Download size={16} />} onClick={launchRouting}>
                      Импорт маршрутов
                    </Button>
                    <div className="ma-link-hint">Российские сайты — напрямую, остальное — через VPN</div>
                  </div>
                )}

                {data.win_sub_deeplink && (
                  <div className="ma-link-block ma-win-block">
                    <div className="ma-link-label">
                      <Monitor size={14} strokeWidth={2} />
                      Windows — Dem1chVPN (быстрый импорт)
                    </div>
                    <Button variant="subtle" size="md" fullWidth leftIcon={<Download size={16} />} onClick={launchWindows}>
                      Импорт подписки
                    </Button>
                    <div className="ma-link-row ma-link-row--compact">
                      <code className="ma-link-value ma-link-value--small">{data.win_sub_deeplink}</code>
                      <CopyButton text={data.win_sub_deeplink} />
                    </div>
                  </div>
                )}

                {data.vless_url && (
                  <div className="ma-link-block">
                    <div className="ma-link-label">
                      <LinkIcon size={14} strokeWidth={2} />
                      Прямая VLESS ссылка
                    </div>
                    <div className="ma-link-row">
                      <code className="ma-link-value ma-link-value--small">{data.vless_url}</code>
                      <CopyButton text={data.vless_url} />
                    </div>
                    <div className="ma-link-hint">Для роутеров (OpenWrt + Passwall2)</div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* PLATFORMS */}
      <motion.div variants={childItem} className="ma-card">
        <div className="ma-card-title">
          <Smartphone size={18} strokeWidth={1.75} />
          Настройка по платформам
        </div>

        <div className="ma-platforms">
          {PLATFORMS.map(p => {
            const Ico = p.icon
            const active = platform === p.id
            return (
              <button
                key={p.id}
                type="button"
                className={`ma-platform-chip ${active ? 'active' : ''}`}
                onClick={() => setPlatform(active ? null : p.id)}
              >
                <Ico size={16} strokeWidth={1.75} />
                <span>{p.label}</span>
              </button>
            )
          })}
        </div>

        <AnimatePresence mode="wait">
          {platform && (
            <motion.div
              key={platform}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ type: 'spring', stiffness: 320, damping: 28 }}
              className="ma-instructions"
            >
              {platform === 'ios' && (
                <>
                  <div className="ma-inst-app">
                    <span>V2RayTun</span>
                    <a href="https://apps.apple.com/app/v2raytun/id6476628951" target="_blank" rel="noopener" className="ma-inst-link">
                      <ExternalLink size={13} /> App Store
                    </a>
                  </div>
                  <ol className="ma-steps">
                    <li>Установите <strong>V2RayTun</strong> из App Store</li>
                    <li>Нажмите <strong>«Импорт подписки»</strong> выше — откроется приложение</li>
                    <li>Нажмите <strong>«Импорт маршрутов»</strong> — добавятся правила маршрутизации</li>
                    <li>Включите VPN и разрешите VPN-профиль</li>
                  </ol>
                  <div className="ma-inst-note">Если deeplink не работает — скопируйте URL подписки и вставьте вручную: V2RayTun → ☰ → Подписка → +</div>
                </>
              )}

              {platform === 'android' && (
                <>
                  <div className="ma-inst-app">
                    <span>v2rayNG</span>
                    <a href="https://play.google.com/store/apps/details?id=com.v2ray.ang" target="_blank" rel="noopener" className="ma-inst-link">
                      <ExternalLink size={13} /> Google Play
                    </a>
                  </div>
                  <ol className="ma-steps">
                    <li>Установите <strong>v2rayNG</strong> из Google Play</li>
                    <li>Скопируйте URL подписки из раздела выше</li>
                    <li>v2rayNG → ☰ → <strong>Подписка → +</strong> → вставьте URL</li>
                    <li>Потяните список вниз для обновления</li>
                  </ol>
                </>
              )}

              {platform === 'windows' && (
                <>
                  <div className="ma-inst-app">
                    <span>Dem1chVPN</span>
                    <a
                      href="https://github.com/HotFies/Dem1chVPN/releases/download/demichvpn-win-v.1.0.0/Dem1chVPN-1.0.0-Setup.exe"
                      target="_blank" rel="noopener" className="ma-inst-link"
                    >
                      <ExternalLink size={13} /> Скачать
                    </a>
                  </div>
                  <ol className="ma-steps">
                    <li>Скачайте <strong>Dem1chVPN-Setup.exe</strong></li>
                    <li>Запустите установщик и следуйте инструкциям</li>
                    <li>Нажмите <strong>«Импорт подписки»</strong> в разделе Windows выше</li>
                    <li>Или скопируйте URL подписки и вставьте в настройках приложения</li>
                  </ol>
                  <div className="ma-inst-note">
                    Альтернатива: <a href="https://github.com/2dust/v2rayN/releases" target="_blank" rel="noopener">v2rayN</a> → Subscription → Add → вставьте URL подписки
                  </div>
                </>
              )}

              {platform === 'macos' && (
                <>
                  <div className="ma-inst-app">
                    <span>V2RayTun</span>
                    <a href="https://apps.apple.com/app/v2raytun/id6476628951" target="_blank" rel="noopener" className="ma-inst-link">
                      <ExternalLink size={13} /> App Store
                    </a>
                  </div>
                  <ol className="ma-steps">
                    <li>Установите <strong>V2RayTun</strong> из App Store</li>
                    <li>Нажмите «Импорт подписки» выше, или скопируйте URL</li>
                    <li>V2RayTun → Подписка → + → вставьте URL</li>
                    <li>Нажмите кнопку подключения и разрешите VPN-профиль</li>
                  </ol>
                </>
              )}

              {platform === 'router' && (
                <>
                  <div className="ma-inst-app">
                    <span>OpenWrt + Passwall2</span>
                  </div>
                  <ol className="ma-steps">
                    <li>Убедитесь, что на роутере установлен <strong>OpenWrt</strong></li>
                    <li>Установите <strong>Passwall2</strong> через opkg</li>
                    <li>Скопируйте прямую VLESS-ссылку из раздела выше</li>
                    <li>Passwall2 → Servers → Import URL → вставьте ссылку</li>
                  </ol>
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* FAQ */}
      <motion.div variants={childItem} className="ma-card">
        <div className="ma-card-title">
          <HelpCircle size={18} strokeWidth={1.75} />
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
      </motion.div>
    </motion.div>
  )
}
