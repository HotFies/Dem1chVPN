import { lazy, Suspense, useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  LayoutDashboard,
  Users,
  Network,
  Settings as SettingsIcon,
  MessageSquare,
  LifeBuoy,
  ShieldCheck,
} from 'lucide-react'
import Dashboard from './components/Dashboard'
import UserList from './components/UserList'
import RouteManager from './components/RouteManager'
import Settings from './components/Settings'
import Tickets from './components/Tickets'
import HelpCenter from './components/HelpCenter'
import MyAccount from './components/MyAccount'
const AppStoreGuide = lazy(() => import('./components/AppStoreGuide'))
import { ToastProvider } from './hooks/useToast'
import { ConfirmProvider } from './hooks/useConfirm'
import { useAuth } from './hooks/useAuth'
import { useHaptic } from './hooks/useHaptic'
import { AuthSkeleton } from './components/AuthSkeleton'

type Page = 'dashboard' | 'users' | 'routes' | 'settings' | 'tickets' | 'help' | 'account'

const validPages: Page[] = ['dashboard', 'users', 'routes', 'tickets', 'settings', 'help', 'account']

function getInitialPage(): Page {
  const tg = (window as any).Telegram?.WebApp
  const urlParams = new URLSearchParams(window.location.search)
  const qPage = urlParams.get('page')
  if (qPage && (validPages as string[]).includes(qPage)) return qPage as Page

  const startParam = tg?.initDataUnsafe?.start_param
  if (startParam && (validPages as string[]).includes(startParam)) return startParam as Page

  const hash = window.location.hash.replace('#', '')
  if (hash && (validPages as string[]).includes(hash)) return hash as Page

  return 'dashboard'
}

function getInitialGuide(): boolean {
  const tg = (window as any).Telegram?.WebApp
  const urlParams = new URLSearchParams(window.location.search)
  if (urlParams.get('page') === 'appstore-guide') return true
  if (tg?.initDataUnsafe?.start_param === 'appstore-guide') return true
  if (window.location.hash.replace('#', '') === 'appstore-guide') return true
  return false
}

const NAV_ITEMS: { key: Page; icon: typeof LayoutDashboard; label: string }[] = [
  { key: 'dashboard', icon: LayoutDashboard, label: 'Панель' },
  { key: 'users', icon: Users, label: 'Юзеры' },
  { key: 'routes', icon: Network, label: 'Роуты' },
  { key: 'tickets', icon: MessageSquare, label: 'Тикеты' },
  { key: 'settings', icon: SettingsIcon, label: 'Настр.' },
  { key: 'help', icon: LifeBuoy, label: 'Помощь' },
  { key: 'account', icon: ShieldCheck, label: 'Кабинет' },
]

const PAGE_TITLES: Record<Page, string> = {
  dashboard: 'Панель управления',
  users: 'Пользователи',
  routes: 'Маршрутизация',
  tickets: 'Тикеты',
  settings: 'Настройки',
  help: 'Помощь',
  account: 'Мой аккаунт',
}

const ADMIN_PAGES: Page[] = ['dashboard', 'users', 'routes', 'tickets', 'settings', 'help']
const USER_PAGES: Page[] = ['account', 'tickets', 'help']

function AppShell() {
  const { loaded, isAdmin } = useAuth()
  const [page, setPage] = useState<Page>(getInitialPage())
  const [showGuide, setShowGuide] = useState(getInitialGuide())
  const h = useHaptic()

  useEffect(() => {
    if (loaded && !isAdmin && page === 'dashboard') setPage('account')
  }, [loaded, isAdmin, page])

  const pages = (isAdmin ? ADMIN_PAGES : USER_PAGES)
  const navItems = NAV_ITEMS.filter(n => pages.includes(n.key))

  const handleNav = (next: Page) => {
    if (next === page) return
    h.selection()
    setPage(next)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-logo">
          <ShieldCheck size={24} strokeWidth={1.75} className="header-shield" aria-hidden />
          <span className="header-brand">Dem1chVPN</span>
          <span className="header-dot" aria-hidden />
        </div>
      </header>

      <main className="app-main" aria-labelledby="page-title">
        <h1 id="page-title" className="sr-only">{PAGE_TITLES[page]}</h1>
        {!loaded ? (
          <AuthSkeleton />
        ) : (
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={page}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ type: 'spring', stiffness: 320, damping: 28, mass: 0.6 }}
              className="page-frame"
            >
              {page === 'dashboard' && isAdmin && <Dashboard />}
              {page === 'users' && isAdmin && <UserList />}
              {page === 'routes' && isAdmin && <RouteManager />}
              {page === 'settings' && isAdmin && <Settings />}
              {page === 'tickets' && <Tickets isAdmin={isAdmin} />}
              {page === 'help' && <HelpCenter onOpenGuide={() => setShowGuide(true)} />}
              {page === 'account' && <MyAccount />}
            </motion.div>
          </AnimatePresence>
        )}
      </main>

      {showGuide && (
        <Suspense fallback={null}>
          <AppStoreGuide onBack={() => { setShowGuide(false); window.location.hash = '' }} />
        </Suspense>
      )}

      <nav className="app-nav" aria-label="Главная навигация">
        {navItems.map(item => {
          const active = item.key === page
          const Ico = item.icon
          return (
            <button
              key={item.key}
              className={`nav-btn${active ? ' active' : ''}`}
              onClick={() => handleNav(item.key)}
              aria-current={active ? 'page' : undefined}
              aria-label={item.label}
            >
              {active && (
                <motion.span
                  layoutId="nav-pill"
                  className="nav-pill"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
              <span className="nav-btn-content">
                <Ico size={22} strokeWidth={active ? 2 : 1.6} />
                <span>{item.label}</span>
              </span>
            </button>
          )
        })}
      </nav>
    </div>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <ConfirmProvider>
        <AppShell />
      </ConfirmProvider>
    </ToastProvider>
  )
}
