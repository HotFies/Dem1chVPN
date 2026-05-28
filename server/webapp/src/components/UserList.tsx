import { useEffect, useMemo, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Users,
  Link as LinkIcon,
  Network as NetworkIcon,
  Pause,
  Play,
  Search,
  ArrowUpDown,
} from 'lucide-react'
import { getUsers, getUserLink, toggleUser, formatBytes, type User } from '../api/client'
import { Sheet } from './ui/Sheet'
import { CopyButton } from './ui/CopyButton'
import { Button } from './ui/Button'
import { Skeleton } from './ui/Skeleton'
import { Tabs } from './ui/Tabs'
import { StatusPill } from './ui/StatusPill'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'

type SortKey = 'name' | 'traffic' | 'expiry'
type FilterKey = 'all' | 'active' | 'disabled'

function trafficRatio(u: User): number {
  if (!u.traffic_limit) return 0
  return Math.min(u.traffic_total / u.traffic_limit, 1.5)
}

export default function UserList() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<FilterKey>('all')
  const [sort, setSort] = useState<SortKey>('name')
  const [search, setSearch] = useState('')
  const [linkData, setLinkData] = useState<{ user: User; vlessUrl: string; subUrl: string } | null>(null)
  const [toggling, setToggling] = useState<number | null>(null)
  const toast = useToast()
  const confirm = useConfirm()

  useEffect(() => {
    getUsers()
      .then(d => { setUsers(d.users || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const handleLink = useCallback(async (user: User) => {
    try {
      const data = await getUserLink(user.id)
      setLinkData({ user, vlessUrl: data.vless_url, subUrl: data.sub_url })
    } catch {
      toast.error('Не удалось получить ссылки')
    }
  }, [toast])

  const handleToggle = useCallback(async (user: User) => {
    if (toggling !== null) return
    if (user.active) {
      const ok = await confirm({
        title: `Отключить ${user.name}?`,
        description: 'Пользователь не сможет подключаться к VPN до повторной активации.',
        confirmLabel: 'Отключить',
        destructive: true,
      })
      if (!ok) return
    }
    setToggling(user.id)
    setUsers(prev => prev.map(u => u.id === user.id ? { ...u, active: !u.active } : u))
    try {
      const result = await toggleUser(user.id)
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, active: result.active } : u))
      toast.success(result.active ? 'Активирован' : 'Отключён')
    } catch {
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, active: user.active } : u))
      toast.error('Не удалось переключить')
    } finally {
      setToggling(null)
    }
  }, [toggling, toast, confirm])

  const visible = useMemo(() => {
    let arr = users
    if (filter === 'active') arr = arr.filter(u => u.active)
    else if (filter === 'disabled') arr = arr.filter(u => !u.active)
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      arr = arr.filter(u => u.name.toLowerCase().includes(q))
    }
    arr = [...arr].sort((a, b) => {
      if (sort === 'name') return a.name.localeCompare(b.name)
      if (sort === 'traffic') return trafficRatio(b) - trafficRatio(a)
      // expiry: ближайший раньше; nullable бессрочный → в конец
      const ax = a.expiry ? new Date(a.expiry).getTime() : Number.POSITIVE_INFINITY
      const bx = b.expiry ? new Date(b.expiry).getTime() : Number.POSITIVE_INFINITY
      return ax - bx
    })
    return arr
  }, [users, filter, sort, search])

  if (loading) {
    return (
      <div className="user-list">
        <div className="section-header">
          <div className="section-icon"><Users size={22} strokeWidth={1.75} /></div>
          <h2>Пользователи</h2>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} height={120} radius="lg" />)}
        </div>
      </div>
    )
  }

  const activeCount = users.filter(u => u.active).length
  const disabledCount = users.length - activeCount

  return (
    <div className="user-list">
      <div className="section-header">
        <div className="section-icon"><Users size={22} strokeWidth={1.75} /></div>
        <h2>
          Пользователи
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 14, color: 'var(--text-secondary)', fontWeight: 400, marginLeft: 6 }}>
            ({users.length})
          </span>
        </h2>
      </div>

      <div className="user-controls">
        <div className="user-search">
          <label htmlFor="users-search" className="sr-only">Поиск по имени</label>
          <Search size={16} strokeWidth={2} className="user-search-icon" aria-hidden />
          <input
            id="users-search"
            type="search"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Поиск по имени…"
            className="user-search-input"
            inputMode="search"
            autoCapitalize="off"
            autoCorrect="off"
          />
        </div>
        <div className="user-sort">
          <label htmlFor="users-sort" className="sr-only">Сортировка</label>
          <ArrowUpDown size={14} strokeWidth={2} aria-hidden />
          <select id="users-sort" aria-label="Сортировка" value={sort} onChange={e => setSort(e.target.value as SortKey)}>
            <option value="name">По имени</option>
            <option value="traffic">По трафику</option>
            <option value="expiry">По сроку</option>
          </select>
        </div>
      </div>

      <Tabs<FilterKey>
        items={[
          { key: 'all', label: 'Все', count: users.length },
          { key: 'active', label: 'Активные', count: activeCount },
          { key: 'disabled', label: 'Отключённые', count: disabledCount },
        ]}
        value={filter}
        onChange={setFilter}
        layoutId="users-tabs"
      />

      {visible.length === 0 ? (
        <div className="empty-state" style={{ marginTop: 16 }}>
          <Users size={48} strokeWidth={1.5} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.3 }} />
          {search ? 'Никого не найдено' : 'Нет пользователей'}
        </div>
      ) : (
        <motion.div className="card-list" layout style={{ marginTop: 12 }}>
          <AnimatePresence initial={false}>
            {visible.map(u => {
              const pct = u.traffic_limit ? Math.min((u.traffic_total / u.traffic_limit) * 100, 100) : 0
              const overload = u.traffic_limit && u.traffic_total > u.traffic_limit * 0.8
              return (
                <motion.div
                  key={u.id}
                  layout
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.16 } }}
                  transition={{ type: 'spring', stiffness: 260, damping: 26 }}
                  className={`user-card ${u.active ? '' : 'disabled'}`}
                >
                  <div className="user-card-header">
                    <StatusPill tone={u.active ? 'active' : 'inactive'} pulse>
                      {u.active ? 'Онлайн' : 'Откл.'}
                    </StatusPill>
                    <span className="user-name">{u.name}</span>
                  </div>

                  <div className="user-card-body">
                    <div className="stat-row">
                      <span>Трафик</span>
                      <span className="num">{formatBytes(u.traffic_total)} / {u.traffic_limit ? formatBytes(u.traffic_limit) : '∞'}</span>
                    </div>
                    {u.traffic_limit && (
                      <div className="progress-bar">
                        <motion.div
                          className="progress-fill"
                          initial={{ scaleX: 0 }}
                          animate={{ scaleX: pct / 100 }}
                          transition={{ type: 'spring', stiffness: 110, damping: 22 }}
                          style={{
                            width: '100%',
                            transformOrigin: 'left center',
                            background: overload
                              ? 'linear-gradient(90deg, var(--danger), var(--danger-light))'
                              : 'linear-gradient(90deg, var(--accent), var(--violet))',
                          }}
                        />
                      </div>
                    )}
                    <div className="stat-row">
                      <span>Срок</span>
                      <span className="num">{u.expiry || '∞ Бессрочно'}</span>
                    </div>
                  </div>

                  <div className="user-card-actions">
                    <Button size="sm" variant="ghost" leftIcon={<LinkIcon size={14} />} onClick={() => handleLink(u)}>
                      Ссылка
                    </Button>
                    <Button
                      size="sm"
                      variant={u.active ? 'danger' : 'success'}
                      loading={toggling === u.id}
                      leftIcon={!toggling && (u.active ? <Pause size={14} /> : <Play size={14} />)}
                      onClick={() => handleToggle(u)}
                    >
                      {u.active ? 'Откл.' : 'Вкл.'}
                    </Button>
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Sheet со ссылками */}
      <Sheet
        open={linkData != null}
        onClose={() => setLinkData(null)}
        title={linkData ? `Ссылки — ${linkData.user.name}` : ''}
      >
        {linkData && (
          <div className="link-sheet">
            <div className="link-section">
              <span className="link-label"><NetworkIcon size={13} strokeWidth={2} /> Подписка (рекомендуется)</span>
              <div className="link-row">
                <code className="link-value">{linkData.subUrl}</code>
                <CopyButton text={linkData.subUrl} />
              </div>
            </div>
            <div className="link-section">
              <span className="link-label"><LinkIcon size={13} strokeWidth={2} /> Прямая ссылка VLESS</span>
              <div className="link-row">
                <code className="link-value">{linkData.vlessUrl}</code>
                <CopyButton text={linkData.vlessUrl} />
              </div>
            </div>
          </div>
        )}
      </Sheet>

    </div>
  )
}
