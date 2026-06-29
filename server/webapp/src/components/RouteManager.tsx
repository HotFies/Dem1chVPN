import { useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Network as NetworkIcon,
  Globe,
  Plus,
  Trash2,
  Search,
} from 'lucide-react'
import { getRoutes, addRoute, deleteRoute, type RouteRule } from '../api/client'
import { Button } from './ui/Button'
import { IconButton } from './ui/IconButton'
import { Tabs } from './ui/Tabs'
import { Skeleton } from './ui/Skeleton'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { useDebounce } from '../hooks/useDebounce'

const PAGE_SIZE = 50

type Filter = 'all' | 'proxy' | 'direct'

export default function RouteManager() {
  const [rules, setRules] = useState<RouteRule[]>([])
  const [newDomain, setNewDomain] = useState('')
  const [filter, setFilter] = useState<Filter>('all')
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounce(search, 200)
  const [loading, setLoading] = useState(true)
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)
  const sentinelRef = useRef<HTMLDivElement | null>(null)
  const toast = useToast()
  const confirm = useConfirm()

  const loadRules = () => {
    getRoutes()
      .then(d => { setRules(d.rules || []); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(() => { loadRules() }, [])
  useEffect(() => { setVisibleCount(PAGE_SIZE) }, [filter, debouncedSearch])

  const filtered = useMemo(() => {
    return rules
      .filter(r => filter === 'all' || r.rule_type === filter)
      .filter(r => !debouncedSearch || r.domain.toLowerCase().includes(debouncedSearch.toLowerCase()))
  }, [rules, filter, debouncedSearch])

  const visible = filtered.slice(0, visibleCount)
  const hasMore = visibleCount < filtered.length

  // intersection observer для авто-подгрузки
  useEffect(() => {
    if (!hasMore || !sentinelRef.current) return
    const obs = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) setVisibleCount(v => v + PAGE_SIZE)
    }, { rootMargin: '120px' })
    obs.observe(sentinelRef.current)
    return () => obs.disconnect()
  }, [hasMore, visibleCount])

  const handleAddDomain = async (type: 'proxy' | 'direct') => {
    const v = newDomain.trim()
    if (!v) return
    try {
      await addRoute(v, type)
      setNewDomain('')
      toast.success(`Маршрут добавлен (${type === 'proxy' ? 'через прокси' : 'напрямую'})`)
      loadRules()
    } catch {
      toast.error('Не удалось добавить домен')
    }
  }

  const handleDelete = async (domain: string) => {
    const ok = await confirm({
      title: 'Удалить маршрут?',
      description: `Правило для ${domain} будет удалено.`,
      confirmLabel: 'Удалить',
      destructive: true,
    })
    if (!ok) return
    setRules(prev => prev.filter(r => r.domain !== domain))
    try {
      await deleteRoute(domain)
      toast.success('Маршрут удалён')
    } catch {
      toast.error('Не удалось удалить')
      loadRules()
    }
  }

  const proxyCount = rules.filter(r => r.rule_type === 'proxy').length
  const directCount = rules.filter(r => r.rule_type === 'direct').length

  return (
    <div className="route-manager">
      <div className="section-header">
        <div className="section-icon"><NetworkIcon size={22} strokeWidth={1.75} /></div>
        <h2>Маршрутизация</h2>
      </div>

      <div className="add-domain-form">
        <input
          type="text"
          value={newDomain}
          onChange={e => setNewDomain(e.target.value)}
          placeholder="example.com"
          className="domain-input"
          inputMode="url"
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
          onKeyDown={e => { if (e.key === 'Enter') handleAddDomain('proxy') }}
        />
        <div className="btn-group">
          <Button size="sm" variant="subtle" leftIcon={<Plus size={14} />} onClick={() => handleAddDomain('proxy')}>
            Прокси
          </Button>
          <Button size="sm" variant="ghost" leftIcon={<Globe size={14} />} onClick={() => handleAddDomain('direct')}>
            Напрямую
          </Button>
        </div>
      </div>

      <Tabs<Filter>
        items={[
          { key: 'all', label: 'Все', count: rules.length },
          { key: 'proxy', label: 'Прокси', count: proxyCount },
          { key: 'direct', label: 'Напрямую', count: directCount },
        ]}
        value={filter}
        onChange={setFilter}
        layoutId="routes-tabs"
      />

      {rules.length > 20 && (
        <div className="user-search" style={{ marginTop: 10 }}>
          <label htmlFor="routes-search" className="sr-only">Поиск домена</label>
          <Search size={16} strokeWidth={2} className="user-search-icon" aria-hidden />
          <input
            id="routes-search"
            type="search"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Поиск домена…"
            className="user-search-input"
            inputMode="search"
            autoCapitalize="off"
            autoCorrect="off"
            spellCheck={false}
          />
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 12 }}>
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} height={48} radius="md" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">{debouncedSearch ? 'Ничего не найдено' : 'Нет маршрутов'}</div>
      ) : (
        <motion.div className="rule-list" layout style={{ marginTop: 12 }}>
          <AnimatePresence initial={false}>
            {visible.map(r => (
              <motion.div
                key={r.id}
                layout
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: 80, transition: { duration: 0.18 } }}
                transition={{ type: 'spring', stiffness: 320, damping: 28 }}
                className="rule-item"
              >
                <span className={`rule-type ${r.rule_type}`}>
                  <span className="rule-dot" />
                  {r.rule_type === 'proxy' ? 'Прокси' : 'Прямой'}
                </span>
                <span className="rule-domain">{r.domain}</span>
                <span className="rule-source">{r.added_by}</span>
                <IconButton aria-label="Удалить" variant="danger" size="sm" onClick={() => handleDelete(r.domain)}>
                  <Trash2 size={14} strokeWidth={2} />
                </IconButton>
              </motion.div>
            ))}
          </AnimatePresence>
          {hasMore && <div ref={sentinelRef} style={{ height: 1 }} />}
        </motion.div>
      )}
    </div>
  )
}
