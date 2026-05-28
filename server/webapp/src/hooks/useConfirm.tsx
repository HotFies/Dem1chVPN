import React, { createContext, useCallback, useContext, useRef, useState } from 'react'
import { Sheet } from '../components/ui/Sheet'
import { Button } from '../components/ui/Button'

type ConfirmOptions = {
  title: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  destructive?: boolean
}

type Resolver = (v: boolean) => void

type ConfirmCtx = (opts: ConfirmOptions) => Promise<boolean>

const Ctx = createContext<ConfirmCtx | null>(null)

export function ConfirmProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<{ open: boolean; opts: ConfirmOptions | null }>({ open: false, opts: null })
  const resolverRef = useRef<Resolver | null>(null)

  const confirm = useCallback((opts: ConfirmOptions) => {
    return new Promise<boolean>(resolve => {
      resolverRef.current = resolve
      setState({ open: true, opts })
    })
  }, [])

  const close = (result: boolean) => {
    resolverRef.current?.(result)
    resolverRef.current = null
    setState(prev => ({ ...prev, open: false }))
  }

  const opts = state.opts

  return (
    <Ctx.Provider value={confirm}>
      {children}
      <Sheet
        open={state.open}
        onClose={() => close(false)}
        title={opts?.title}
        size="auto"
        footer={
          <div className="confirm-actions">
            <Button variant="ghost" fullWidth onClick={() => close(false)}>
              {opts?.cancelLabel ?? 'Отмена'}
            </Button>
            <Button
              variant={opts?.destructive ? 'danger' : 'primary'}
              fullWidth
              onClick={() => close(true)}
            >
              {opts?.confirmLabel ?? 'Подтвердить'}
            </Button>
          </div>
        }
      >
        {opts?.description && <p className="confirm-desc">{opts.description}</p>}
      </Sheet>
    </Ctx.Provider>
  )
}

export function useConfirm(): ConfirmCtx {
  const c = useContext(Ctx)
  if (!c) throw new Error('useConfirm must be used within ConfirmProvider')
  return c
}
