import { useCallback, useEffect, useRef, useState } from 'react'

type Options = {
  intervalMs: number
  enabled?: boolean
  pauseWhenHidden?: boolean
}

export function usePollingQuery<T>(
  fetcher: (signal?: AbortSignal) => Promise<T>,
  deps: any[],
  { intervalMs, enabled = true, pauseWhenHidden = true }: Options,
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<unknown>(null)
  const [refreshing, setRefreshing] = useState(false)
  const mounted = useRef(true)
  const lastFetched = useRef(0)
  const abortRef = useRef<AbortController | null>(null)

  const run = useCallback(async (silent = false) => {
    // отменяем in-flight чтобы не было гонок
    abortRef.current?.abort()
    const ac = new AbortController()
    abortRef.current = ac

    if (!silent) setLoading(prev => (data == null ? true : prev))
    if (silent) setRefreshing(true)
    try {
      const v = await fetcher(ac.signal)
      if (!mounted.current || ac.signal.aborted) return
      setData(v)
      setError(null)
    } catch (e: any) {
      if (e?.name === 'AbortError') return
      if (!mounted.current) return
      setError(e)
    } finally {
      if (mounted.current && !ac.signal.aborted) {
        setLoading(false)
        setRefreshing(false)
        lastFetched.current = Date.now()
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
      abortRef.current?.abort()
    }
  }, [])

  useEffect(() => {
    if (!enabled) return
    run(false)
    let timer: number | undefined

    const start = () => {
      if (timer) return
      timer = window.setInterval(() => {
        if (pauseWhenHidden && document.visibilityState === 'hidden') return
        run(true)
      }, intervalMs)
    }
    const stop = () => {
      if (timer) window.clearInterval(timer)
      timer = undefined
    }
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        if (Date.now() - lastFetched.current > intervalMs) run(true)
        start()
      } else if (pauseWhenHidden) {
        stop()
      }
    }

    start()
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      stop()
      document.removeEventListener('visibilitychange', onVisibility)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, intervalMs, run])

  return { data, loading, error, refreshing, refresh: () => run(true) }
}
