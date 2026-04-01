import React, { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import UserList from './components/UserList'
import RouteManager from './components/RouteManager'
import Settings from './components/Settings'
import Tickets from './components/Tickets'

type Page = 'dashboard' | 'users' | 'routes' | 'settings' | 'tickets'

const tg = (window as any).Telegram?.WebApp

function App() {
  // Check if opened with #tickets hash (from bot WebApp button)
  const initialPage = window.location.hash === '#tickets' ? 'tickets' : 'dashboard'
  const [page, setPage] = useState<Page>(initialPage as Page)
  const [isAdmin, setIsAdmin] = useState(false)
  const [userId, setUserId] = useState<number | null>(null)

  useEffect(() => {
    // Check admin status from initData
    if (tg?.initDataUnsafe?.user) {
      fetch('/api/auth/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: tg.initData }),
      })
        .then(r => r.json())
        .then(data => {
          setIsAdmin(data.is_admin || false)
          setUserId(data.user_id || null)
        })
        .catch(() => setIsAdmin(false))
    }
  }, [])

  // Admin pages
  const adminPages = ['dashboard', 'users', 'routes', 'tickets', 'settings'] as const
  // User pages — only tickets
  const userPages = ['tickets'] as const
  const pages = isAdmin ? adminPages : userPages

  const pageIcons: Record<string, string> = {
    dashboard: '📊', users: '👥', routes: '🔀',
    tickets: '🎫', settings: '⚙️',
  }
  const pageLabels: Record<string, string> = {
    dashboard: 'Dashboard', users: 'Users', routes: 'Routes',
    tickets: 'Тикеты', settings: 'Settings',
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🛡️ Dem1chVPN</h1>
      </header>

      <nav className="app-nav">
        {pages.map(p => (
          <button
            key={p}
            className={`nav-btn ${page === p ? 'active' : ''}`}
            onClick={() => setPage(p)}
          >
            {pageIcons[p]}
            <span>{pageLabels[p]}</span>
          </button>
        ))}
      </nav>

      <main className="app-main">
        {page === 'dashboard' && isAdmin && <Dashboard />}
        {page === 'users' && isAdmin && <UserList />}
        {page === 'routes' && isAdmin && <RouteManager />}
        {page === 'settings' && isAdmin && <Settings />}
        {page === 'tickets' && <Tickets isAdmin={isAdmin} />}
      </main>
    </div>
  )
}

export default App

