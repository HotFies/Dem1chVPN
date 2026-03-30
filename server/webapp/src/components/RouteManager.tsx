import React, { useState, useEffect } from 'react'

interface RouteRule { id: number; domain: string; rule_type: string; added_by: string }

export default function RouteManager() {
  const [rules, setRules] = useState<RouteRule[]>([])
  const [newDomain, setNewDomain] = useState('')
  const [filter, setFilter] = useState<'all' | 'proxy' | 'direct'>('all')
  const [loading, setLoading] = useState(true)

  const loadRules = () => {
    fetch('/api/routes')
      .then(r => r.json())
      .then(data => { setRules(data.rules || []); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(() => { loadRules() }, [])

  const addDomain = async (type: 'proxy' | 'direct') => {
    if (!newDomain.trim()) return
    await fetch('/api/routes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain: newDomain.trim(), type }),
    })
    setNewDomain('')
    loadRules()
  }

  const deleteDomain = async (domain: string) => {
    await fetch(`/api/routes/${domain}`, { method: 'DELETE' })
    loadRules()
  }

  const filtered = rules.filter(r => filter === 'all' || r.rule_type === filter)

  return (
    <div className="route-manager">
      <div className="section-header"><h2>🔀 Маршрутизация</h2></div>

      <div className="add-domain-form">
        <input
          type="text" value={newDomain}
          onChange={e => setNewDomain(e.target.value)}
          placeholder="example.com"
          className="domain-input"
        />
        <div className="btn-group">
          <button className="btn-proxy" onClick={() => addDomain('proxy')}>🔵 PROXY</button>
          <button className="btn-direct" onClick={() => addDomain('direct')}>🟢 DIRECT</button>
        </div>
      </div>

      <div className="filter-tabs">
        {(['all', 'proxy', 'direct'] as const).map(f => (
          <button key={f} className={`filter-tab ${filter === f ? 'active' : ''}`}
                  onClick={() => setFilter(f)}>
            {{ all: '📋 Все', proxy: '🔵 Proxy', direct: '🟢 Direct' }[f]}
            <span className="count">
              {f === 'all' ? rules.length : rules.filter(r => r.rule_type === f).length}
            </span>
          </button>
        ))}
      </div>

      {loading ? <div className="loading">⏳</div> : (
        <div className="rule-list">
          {filtered.map(r => (
            <div key={r.id} className="rule-item">
              <span className={`rule-type ${r.rule_type}`}>
                {r.rule_type === 'proxy' ? '🔵' : '🟢'}
              </span>
              <span className="rule-domain">{r.domain}</span>
              <span className="rule-source">{r.added_by}</span>
              <button className="btn-delete" onClick={() => deleteDomain(r.domain)}>🗑️</button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
