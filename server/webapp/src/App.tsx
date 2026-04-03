import React, { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import UserList from './components/UserList'
import RouteManager from './components/RouteManager'
import Settings from './components/Settings'
import Tickets from './components/Tickets'
import HelpCenter from './components/HelpCenter'
import MyAccount from './components/MyAccount'

type Page = 'dashboard' | 'users' | 'routes' | 'settings' | 'tickets' | 'help' | 'account'

const tg = (window as any).Telegram?.WebApp

/* ── SVG Nav Icons ── */
const icons = {
  dashboard: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="9" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="16" width="7" height="5" rx="1.5" />
    </svg>
  ),
  users: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  routes: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="18" cy="5" r="3" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="19" r="3" />
      <path d="M8.59 13.51l6.83 3.98" />
      <path d="M15.41 6.51l-6.82 3.98" />
    </svg>
  ),
  tickets: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <path d="M8 10h8" />
      <path d="M8 14h4" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  ),
  help: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  account: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  ),
}

const shieldIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="M9 12l2 2 4-4" stroke="var(--cyan)" />
  </svg>
)

function App() {
  const hash = window.location.hash.replace('#', '');
  const validHashes = ['tickets', 'help', 'account'];
  const initialPage = (validHashes.includes(hash) ? hash : 'dashboard') as Page;
  const [page, setPage] = useState<Page>(initialPage)
  const [isAdmin, setIsAdmin] = useState(false)
  const [authLoaded, setAuthLoaded] = useState(false)
  const [userId, setUserId] = useState<number | null>(null)

  useEffect(() => {
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
          setAuthLoaded(true)
        })
        .catch(() => { setIsAdmin(false); setAuthLoaded(true) })
    } else {
      setAuthLoaded(true)
    }
  }, [])

  const adminPages = ['dashboard', 'users', 'routes', 'tickets', 'settings'] as const
  const userPages = ['account', 'tickets', 'help'] as const
  const pages = isAdmin ? [...adminPages, 'help' as const] : userPages

  // Set default page for non-admin users ONLY after auth is loaded
  useEffect(() => {
    if (authLoaded && !isAdmin && page === 'dashboard') {
      setPage('account');
    }
  }, [authLoaded, isAdmin]);

  const pageLabels: Record<string, string> = {
    dashboard: 'Панель',
    users: 'Юзеры',
    routes: 'Роуты',
    tickets: 'Тикеты',
    settings: 'Настр.',
    help: 'Помощь',
    account: 'Кабинет',
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-logo">
          {shieldIcon}
          <h1>Dem1chVPN</h1>
        </div>
      </header>

      <main className="app-main" key={page}>
        {page === 'dashboard' && isAdmin && <Dashboard />}
        {page === 'users' && isAdmin && <UserList />}
        {page === 'routes' && isAdmin && <RouteManager />}
        {page === 'settings' && isAdmin && <Settings />}
        {page === 'tickets' && <Tickets isAdmin={isAdmin} />}
        {page === 'help' && <HelpCenter />}
        {page === 'account' && <MyAccount />}
      </main>

      <nav className="app-nav">
        {pages.map(p => (
          <button
            key={p}
            className={`nav-btn ${page === p ? 'active' : ''}`}
            onClick={() => setPage(p)}
          >
            {icons[p]}
            <span>{pageLabels[p]}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}

export default App
