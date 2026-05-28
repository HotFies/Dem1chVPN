import { useEffect, useState } from 'react'
import { getTelegram } from './useTelegram'

export type AuthState = {
  loaded: boolean
  isAdmin: boolean
  userId: number | null
}

export function useAuth(): AuthState {
  const [state, setState] = useState<AuthState>({ loaded: false, isAdmin: false, userId: null })

  useEffect(() => {
    const tg = getTelegram()
    if (!tg?.initDataUnsafe?.user) {
      setState({ loaded: true, isAdmin: false, userId: null })
      return
    }
    let canceled = false
    fetch('/api/auth/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initData: tg.initData }),
    })
      .then(r => r.json())
      .then(data => {
        if (canceled) return
        setState({ loaded: true, isAdmin: !!data.is_admin, userId: data.user_id ?? null })
      })
      .catch(() => {
        if (canceled) return
        setState({ loaded: true, isAdmin: false, userId: null })
      })
    return () => { canceled = true }
  }, [])

  return state
}
