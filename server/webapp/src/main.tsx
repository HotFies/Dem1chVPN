import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/index.css'

// Telegram WebApp initialization
const tg = (window as any).Telegram?.WebApp
if (tg) {
  tg.ready()
  tg.expand()
  tg.enableClosingConfirmation()
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
