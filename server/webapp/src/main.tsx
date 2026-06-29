import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/reset.css'
import './styles/tokens.css'
import './styles/index.css'
import './styles/ui.css'

type ThemeParams = {
  bg_color?: string
  text_color?: string
  hint_color?: string
  link_color?: string
  button_color?: string
  button_text_color?: string
  secondary_bg_color?: string
}

function applyTgTheme(params: ThemeParams) {
  const r = document.documentElement
  const map: Array<[keyof ThemeParams, string]> = [
    ['bg_color', '--tg-bg'],
    ['text_color', '--tg-text'],
    ['hint_color', '--tg-hint'],
    ['link_color', '--tg-link'],
    ['button_color', '--tg-button'],
    ['button_text_color', '--tg-button-text'],
    ['secondary_bg_color', '--tg-secondary-bg'],
  ]
  for (const [src, dst] of map) {
    const v = params?.[src]
    if (v) r.style.setProperty(dst, v)
  }
  r.setAttribute('data-tg-theme', '')
  if (params.bg_color) {
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', params.bg_color)
  }
}

const tg = (window as any).Telegram?.WebApp
if (tg) {
  tg.ready()
  tg.expand()
  tg.enableClosingConfirmation()
  if (tg.themeParams) applyTgTheme(tg.themeParams)
  tg.onEvent?.('themeChanged', () => applyTgTheme(tg.themeParams))
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
