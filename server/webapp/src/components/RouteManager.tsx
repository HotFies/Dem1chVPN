import React, { useState, useEffect } from 'react'
import { getRoutes, addRoute, deleteRoute, type RouteRule } from '../api/client'

/* Icons */
const routeIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="18" cy="5" r="3" />
    <circle cx="6" cy="12" r="3" />
    <circle cx="18" cy="19" r="3" />
    <path d="M8.59 13.51l6.83 3.98" />
    <path d="M15.41 6.51l-6.82 3.98" />
  </svg>
)

const trashIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  </svg>
)

const PAGE_SIZE = 50

export default function RouteManager() {
  const [rules, setRules] = useState<RouteRule[]>([])
  const [newDomain, setNewDomain] = useState('')
  const [filter, setFilter] = useState<'all' | 'proxy' | 'direct'>('all')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)

  const loadRules = () => {
    getRoutes()
      .then(data => { setRules(data.rules || []); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(() => { loadRules() }, [])

  // Reset visible count when filter/search changes
  useEffect(() => { setVisibleCount(PAGE_SIZE) }, [filter, search])

  const handleAddDomain = async (type: 'proxy' | 'direct') => {
    if (!newDomain.trim()) return
    await addRoute(newDomain.trim(), type)
    setNewDomain('')
    loadRules()
  }

  const handleDeleteDomain = async (domain: string) => {
    await deleteRoute(domain)
    loadRules()
  }

  const filtered = rules
    .filter(r => filter === 'all' || r.rule_type === filter)
    .filter(r => !search || r.domain.toLowerCase().includes(search.toLowerCase()))

  const visible = filtered.slice(0, visibleCount)
  const hasMore = visibleCount < filtered.length

  const proxyCount = rules.filter(r => r.rule_type === 'proxy').length
  const directCount = rules.filter(r => r.rule_type === 'direct').length

  return (
    <div className="route-manager">
      <div className="section-header">
        <div className="section-icon">{routeIcon}</div>
        <h2>Маршрутизация</h2>
      </div>

      <div className="add-domain-form">
        <input
          type="text"
          value={newDomain}
          onChange={e => setNewDomain(e.target.value)}
          placeholder="example.com"
          className="domain-input"
          onKeyDown={e => {
            if (e.key === 'Enter') handleAddDomain('proxy')
          }}
        />
        <div className="btn-group">
          <button className="btn-proxy" onClick={() => handleAddDomain('proxy')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v8" /><path d="M8 12h8" />
            </svg>
            Прокси
          </button>
          <button className="btn-direct" onClick={() => handleAddDomain('direct')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v8" /><path d="M8 12h8" />
            </svg>
            Напрямую
          </button>
        </div>
      </div>

      <div className="filter-tabs">
        {([
          { key: 'all' as const, label: 'Все', count: rules.length },
          { key: 'proxy' as const, label: 'Прокси', count: proxyCount },
          { key: 'direct' as const, label: 'Напрямую', count: directCount },
        ]).map(f => (
          <button
            key={f.key}
            className={`filter-tab ${filter === f.key ? 'active' : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
            <span className="count">{f.count}</span>
          </button>
        ))}
      </div>

      {/* Search within rules */}
      {rules.length > 20 && (
        <div className="route-search">
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Поиск домена..."
            className="domain-input"
          />
        </div>
      )}

      {loading ? (
        <div className="loading-page">
          <div className="spinner" />
        </div>
      ) : (
        <div className="rule-list">
          {filtered.length === 0 ? (
            <div className="empty-state">{search ? 'Ничего не найдено' : 'Нет маршрутов'}</div>
          ) : (
            <>
              {visible.map(r => (
                <div key={r.id} className="rule-item">
                  <span className={`rule-type ${r.rule_type}`}>
                    {r.rule_type === 'proxy' ? 'PRX' : 'DIR'}
                  </span>
                  <span className="rule-domain">{r.domain}</span>
                  <span className="rule-source">{r.added_by}</span>
                  <button className="btn-delete" onClick={() => handleDeleteDomain(r.domain)}>
                    {trashIcon}
                  </button>
                </div>
              ))}
              {hasMore && (
                <button
                  className="btn-load-more"
                  onClick={() => setVisibleCount(v => v + PAGE_SIZE)}
                >
                  Показать ещё ({filtered.length - visibleCount} осталось)
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

