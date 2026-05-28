import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Settings as SettingsIcon,
  Cloud,
  Shield,
  MessageSquare,
  RefreshCw,
  Globe,
  Save,
  Copy,
  Check,
  LucideIcon,
} from 'lucide-react'
import {
  getSettings, toggleFeature, restartXray, updateGeo, createBackup,
  type Settings as SettingsType,
} from '../api/client'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { useHaptic } from '../hooks/useHaptic'
import { Button } from './ui/Button'
import { MotionToggle } from './ui/MotionToggle'
import { Skeleton } from './ui/Skeleton'

const FEATURE_META: Record<'warp' | 'adguard' | 'mtproto', { title: string; desc: string; icon: LucideIcon; tone: 'accent' | 'success' | 'violet' }> = {
  warp: { title: 'Cloudflare WARP', desc: 'Double-hop приватность', icon: Cloud, tone: 'accent' },
  adguard: { title: 'AdGuard Home', desc: 'Блокировка рекламы и трекеров', icon: Shield, tone: 'success' },
  mtproto: { title: 'MTProto Прокси', desc: 'Прокси для Telegram', icon: MessageSquare, tone: 'violet' },
}

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } },
}
const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 260, damping: 24 } },
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsType | null>(null)
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const toast = useToast()
  const confirm = useConfirm()
  const h = useHaptic()

  useEffect(() => {
    getSettings()
      .then(d => { setSettings(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const handleToggle = async (feature: 'warp' | 'adguard' | 'mtproto', currentlyOn: boolean) => {
    if (toggling) return
    setToggling(feature)
    setSettings(prev => prev ? { ...prev, [`${feature}_enabled`]: !currentlyOn } as SettingsType : null)
    try {
      const result = await toggleFeature(feature)
      setSettings(prev => prev ? { ...prev, [`${feature}_enabled`]: result.enabled } as SettingsType : null)
      h.notify('success')
    } catch (err: any) {
      const msg = err?.message || `Ошибка переключения ${feature}`
      console.error(`Toggle ${feature} failed:`, err)
      setSettings(prev => prev ? { ...prev, [`${feature}_enabled`]: currentlyOn } as SettingsType : null)
      h.notify('error')
      toast.error(msg)
    } finally {
      setToggling(null)
    }
  }

  const ACTION_LABELS: Record<string, { ok: string; fail: string }> = {
    restart: { ok: 'Xray перезапущен', fail: 'Не удалось перезапустить Xray' },
    geo: { ok: 'Гео-базы обновлены', fail: 'Не удалось обновить гео-базы' },
    backup: { ok: 'Бэкап создан', fail: 'Не удалось создать бэкап' },
  }

  const handleAction = async (action: () => Promise<any>, name: string) => {
    if (name === 'restart') {
      const ok = await confirm({
        title: 'Перезапустить Xray?',
        description: 'Все клиенты на короткое время потеряют подключение.',
        confirmLabel: 'Перезапустить',
        destructive: true,
      })
      if (!ok) return
    }
    setActionLoading(name)
    try {
      await action()
      toast.success(ACTION_LABELS[name].ok)
    } catch {
      toast.error(ACTION_LABELS[name].fail)
    } finally {
      setActionLoading(null)
    }
  }

  const handleCopy = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(key)
      h.notify('success')
      setTimeout(() => setCopied(null), 1500)
    } catch {
      toast.error('Не удалось скопировать')
    }
  }

  if (loading) {
    return (
      <div className="settings">
        <div className="section-header">
          <div className="section-icon"><SettingsIcon size={22} strokeWidth={1.75} /></div>
          <h2>Настройки</h2>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} height={68} radius="lg" />)}
        </div>
      </div>
    )
  }

  if (!settings) {
    return <div className="error">Ошибка загрузки настроек</div>
  }

  const features = [
    { key: 'warp' as const, enabled: settings.warp_enabled },
    { key: 'adguard' as const, enabled: settings.adguard_enabled },
    { key: 'mtproto' as const, enabled: settings.mtproto_enabled },
  ]

  return (
    <motion.div className="settings" variants={stagger} initial="hidden" animate="show">
      <div className="section-header">
        <div className="section-icon"><SettingsIcon size={22} strokeWidth={1.75} /></div>
        <h2>Настройки</h2>
      </div>

      <div className="settings-list">
        {features.map(f => {
          const m = FEATURE_META[f.key]
          const Ico = m.icon
          const toneColor = m.tone === 'accent' ? 'var(--accent)' : m.tone === 'success' ? 'var(--success)' : 'var(--violet)'
          return (
            <motion.div
              key={f.key}
              variants={item}
              className={`setting-card ${f.enabled ? 'enabled' : ''}`}
              style={f.enabled ? { borderColor: `color-mix(in srgb, ${toneColor} 22%, transparent)` } : undefined}
            >
              <div className="setting-info">
                <span
                  className="setting-icon"
                  style={{
                    background: `color-mix(in srgb, ${toneColor} 14%, transparent)`,
                    color: toneColor,
                  }}
                >
                  <Ico size={18} strokeWidth={1.75} />
                </span>
                <div>
                  <div className="setting-title">{m.title}</div>
                  <div className="setting-desc">{m.desc}</div>
                </div>
              </div>
              <MotionToggle
                checked={f.enabled}
                onChange={() => handleToggle(f.key, f.enabled)}
                disabled={toggling === f.key}
                tone={m.tone}
                ariaLabel={`Переключить ${m.title}`}
              />
            </motion.div>
          )
        })}
      </div>

      <motion.div variants={item} className="server-info">
        <div className="info-row">
          <span className="info-label">IP сервера</span>
          <button
            type="button"
            className="info-value"
            onClick={() => handleCopy(settings.server_ip, 'ip')}
          >
            <span className="num">{settings.server_ip}</span>
            {copied === 'ip' ? <Check size={12} color="var(--success)" /> : <Copy size={12} />}
          </button>
        </div>
        <div className="info-row">
          <span className="info-label">SNI</span>
          <button
            type="button"
            className="info-value"
            onClick={() => handleCopy(settings.reality_sni, 'sni')}
          >
            <span className="num">{settings.reality_sni}</span>
            {copied === 'sni' ? <Check size={12} color="var(--success)" /> : <Copy size={12} />}
          </button>
        </div>
      </motion.div>

      <motion.div variants={item} className="settings-actions">
        <Button
          variant="ghost" size="lg" fullWidth
          loading={actionLoading === 'restart'}
          disabled={actionLoading !== null && actionLoading !== 'restart'}
          leftIcon={!actionLoading ? <RefreshCw size={18} color="var(--accent)" /> : undefined}
          onClick={() => handleAction(restartXray, 'restart')}
        >
          Перезапуск Xray
        </Button>
        <Button
          variant="ghost" size="lg" fullWidth
          loading={actionLoading === 'geo'}
          disabled={actionLoading !== null && actionLoading !== 'geo'}
          leftIcon={!actionLoading ? <Globe size={18} color="var(--accent)" /> : undefined}
          onClick={() => handleAction(updateGeo, 'geo')}
        >
          Обновить гео-базы
        </Button>
        <Button
          variant="ghost" size="lg" fullWidth
          loading={actionLoading === 'backup'}
          disabled={actionLoading !== null && actionLoading !== 'backup'}
          leftIcon={!actionLoading ? <Save size={18} color="var(--accent)" /> : undefined}
          onClick={() => handleAction(createBackup, 'backup')}
        >
          Создать бэкап
        </Button>
      </motion.div>
    </motion.div>
  )
}
