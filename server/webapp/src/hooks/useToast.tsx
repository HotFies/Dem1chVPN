import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, XCircle, AlertCircle, Info, LucideIcon } from 'lucide-react'

export type ToastKind = 'success' | 'error' | 'warning' | 'info'

type Toast = {
  id: number
  kind: ToastKind
  message: string
  duration: number
}

type ToastCtx = {
  show: (message: string, kind?: ToastKind, duration?: number) => void
  success: (message: string, duration?: number) => void
  error: (message: string, duration?: number) => void
  warning: (message: string, duration?: number) => void
  info: (message: string, duration?: number) => void
}

const Ctx = createContext<ToastCtx | null>(null)

const ICONS: Record<ToastKind, LucideIcon> = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertCircle,
  info: Info,
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const idRef = useRef(0)

  const dismiss = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const show = useCallback((message: string, kind: ToastKind = 'info', duration = 3500) => {
    const id = ++idRef.current
    setToasts(prev => [...prev, { id, kind, message, duration }])
    return id
  }, [])

  const api: ToastCtx = {
    show,
    success: (m, d) => show(m, 'success', d),
    error: (m, d) => show(m, 'error', d),
    warning: (m, d) => show(m, 'warning', d),
    info: (m, d) => show(m, 'info', d),
  }

  return (
    <Ctx.Provider value={api}>
      {children}
      <div className="toast-stack" role="region" aria-live="polite" aria-atomic="false">
        <AnimatePresence initial={false}>
          {toasts.map(t => (
            <ToastItem key={t.id} toast={t} onDismiss={() => dismiss(t.id)} />
          ))}
        </AnimatePresence>
      </div>
    </Ctx.Provider>
  )
}

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  useEffect(() => {
    const tid = setTimeout(onDismiss, toast.duration)
    return () => clearTimeout(tid)
  }, [toast.duration, onDismiss])

  const Icon = ICONS[toast.kind]
  const assertive = toast.kind === 'error'

  return (
    <motion.div
      role={assertive ? 'alert' : 'status'}
      aria-live={assertive ? 'assertive' : 'polite'}
      className={`toast toast--${toast.kind}`}
      initial={{ opacity: 0, y: -16, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.98, transition: { duration: 0.16 } }}
      transition={{ type: 'spring', stiffness: 320, damping: 28 }}
      onClick={onDismiss}
    >
      <Icon size={18} aria-hidden />
      <span>{toast.message}</span>
    </motion.div>
  )
}

export function useToast(): ToastCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
