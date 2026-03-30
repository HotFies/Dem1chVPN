import React, { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import UserList from './components/UserList'
import RouteManager from './components/RouteManager'
import Settings from './components/Settings'

type Page = 'dashboard' | 'users' | 'routes' | 'settings'

const tg = (window as any).Telegram?.WebApp

function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    // Check admin status from initData
    if (tg?.initDataUnsafe?.user) {
      fetch('/api/auth/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: tg.initData }),
      })
        .then(r => r.json())
        .then(data => setIsAdmin(data.is_admin || false))
        .catch(() => setIsAdmin(false))
    }
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>🛡️ XShield</h1>
      </header>

      <nav className="app-nav">
        {(['dashboard', 'users', 'routes', 'settings'] as const).map(p => (
          <button
            key={p}
            className={`nav-btn ${page === p ? 'active' : ''}`}
            onClick={() => setPage(p)}
          >
            {{ dashboard: '📊', users: '👥', routes: '🔀', settings: '⚙️' }[p]}
            <span>{{ dashboard: 'Dashboard', users: 'Users', routes: 'Routes', settings: 'Settings' }[p]}</span>
          </button>
        ))}
      </nav>

      <main className="app-main">
        {page === 'dashboard' && <Dashboard />}
        {page === 'users' && <UserList />}
        {page === 'routes' && <RouteManager />}
        {page === 'settings' && <Settings />}
      </main>
    </div>
  )
}

export default App
