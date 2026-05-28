import React, { useEffect, useRef } from 'react'
import { AnimatePresence, motion, PanInfo, useDragControls } from 'framer-motion'
import { X } from 'lucide-react'
import clsx from 'clsx'
import { IconButton } from './IconButton'
import { useHaptic } from '../../hooks/useHaptic'

type SheetProps = {
  open: boolean
  onClose: () => void
  title?: React.ReactNode
  children: React.ReactNode
  size?: 'auto' | 'tall' | 'full'
  /** показывать grabber на верху */
  grabber?: boolean
  /** допускать ли свайп вниз для закрытия */
  dismissible?: boolean
  /** показать ли крестик в шапке */
  closeButton?: boolean
  footer?: React.ReactNode
  className?: string
}

export function Sheet({
  open,
  onClose,
  title,
  children,
  size = 'auto',
  grabber = true,
  dismissible = true,
  closeButton = true,
  footer,
  className,
}: SheetProps) {
  const dragControls = useDragControls()
  const h = useHaptic()
  const scrollRef = useRef<HTMLDivElement | null>(null)

  // ESC для закрытия
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  // блок скролла body
  useEffect(() => {
    if (!open) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = prev }
  }, [open])

  const onDragEnd = (_: any, info: PanInfo) => {
    if (!dismissible) return
    if (info.offset.y > 120 || info.velocity.y > 600) {
      h.impact('light')
      onClose()
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <div className="sheet-root">
          <motion.div
            className="sheet-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onClick={onClose}
            aria-hidden
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label={typeof title === 'string' ? title : 'Диалог'}
            className={clsx('sheet', `sheet--${size}`, className)}
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', stiffness: 320, damping: 34, mass: 0.7 }}
            drag={dismissible ? 'y' : false}
            dragControls={dragControls}
            dragListener={false}
            dragConstraints={{ top: 0, bottom: 0 }}
            dragElastic={{ top: 0, bottom: 0.4 }}
            onDragEnd={onDragEnd}
          >
            {(grabber || title || closeButton) && (
              <div
                className="sheet-head"
                onPointerDown={(e) => {
                  if (dismissible) dragControls.start(e)
                }}
              >
                {grabber && <span className="sheet-grabber" aria-hidden />}
                {(title || closeButton) && (
                  <div className="sheet-head-row">
                    <h3 className="sheet-title">{title}</h3>
                    {closeButton && (
                      <IconButton aria-label="Закрыть" onClick={onClose} variant="plain" size="sm">
                        <X size={18} />
                      </IconButton>
                    )}
                  </div>
                )}
              </div>
            )}
            <div className="sheet-body" ref={scrollRef}>
              {children}
            </div>
            {footer && <div className="sheet-foot">{footer}</div>}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
