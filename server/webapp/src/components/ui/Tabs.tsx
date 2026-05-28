import React from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import { useHaptic } from '../../hooks/useHaptic'

export type TabItem<T extends string> = {
  key: T
  label: React.ReactNode
  count?: number | null
}

type Props<T extends string> = {
  items: TabItem<T>[]
  value: T
  onChange: (key: T) => void
  layoutId?: string
  fullWidth?: boolean
}

export function Tabs<T extends string>({ items, value, onChange, layoutId = 'tabs-indicator', fullWidth = true }: Props<T>) {
  const h = useHaptic()
  return (
    <div className={clsx('ui-tabs', fullWidth && 'ui-tabs--full')} role="tablist">
      {items.map(item => {
        const active = value === item.key
        return (
          <button
            key={item.key}
            role="tab"
            aria-selected={active}
            className={clsx('ui-tab', active && 'ui-tab--active')}
            onClick={() => {
              if (active) return
              h.selection()
              onChange(item.key)
            }}
          >
            {active && (
              <motion.span
                layoutId={layoutId}
                className="ui-tab-bg"
                transition={{ type: 'spring', stiffness: 380, damping: 30 }}
              />
            )}
            <span className="ui-tab-content">
              {item.label}
              {item.count != null && <span className="ui-tab-count">{item.count}</span>}
            </span>
          </button>
        )
      })}
    </div>
  )
}
