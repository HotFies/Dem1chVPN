import { useEffect, useState } from 'react'

export type TelegramWebApp = {
  initData: string
  initDataUnsafe: any
  themeParams: Record<string, string>
  colorScheme: 'light' | 'dark'
  viewportHeight: number
  viewportStableHeight: number
  isExpanded: boolean
  platform: string
  version: string
  ready: () => void
  expand: () => void
  close: () => void
  openLink: (url: string) => void
  openTelegramLink: (url: string) => void
  enableClosingConfirmation: () => void
  disableClosingConfirmation: () => void
  onEvent: (event: string, handler: () => void) => void
  offEvent: (event: string, handler: () => void) => void
  HapticFeedback?: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
    selectionChanged: () => void
  }
  MainButton?: {
    text: string
    show: () => void
    hide: () => void
    enable: () => void
    disable: () => void
    onClick: (cb: () => void) => void
    offClick: (cb: () => void) => void
    setText: (text: string) => void
    showProgress: (leaveActive?: boolean) => void
    hideProgress: () => void
  }
  BackButton?: {
    show: () => void
    hide: () => void
    onClick: (cb: () => void) => void
    offClick: (cb: () => void) => void
  }
}

export function getTelegram(): TelegramWebApp | null {
  return (window as any).Telegram?.WebApp ?? null
}

export function useTelegram() {
  const [tg] = useState(() => getTelegram())
  const [viewportHeight, setViewportHeight] = useState(tg?.viewportStableHeight ?? window.innerHeight)

  useEffect(() => {
    if (!tg) return
    const onResize = () => setViewportHeight(tg.viewportStableHeight)
    tg.onEvent?.('viewportChanged', onResize)
    return () => tg.offEvent?.('viewportChanged', onResize)
  }, [tg])

  return { tg, isTelegram: tg != null, viewportHeight }
}
