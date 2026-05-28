import { motion } from 'framer-motion'
import clsx from 'clsx'
import { useHaptic } from '../../hooks/useHaptic'

type Props = {
  checked: boolean
  onChange: (v: boolean) => void
  disabled?: boolean
  ariaLabel?: string
  tone?: 'accent' | 'success' | 'warning' | 'violet'
}

export function MotionToggle({ checked, onChange, disabled, ariaLabel, tone = 'accent' }: Props) {
  const h = useHaptic()
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel}
      disabled={disabled}
      className={clsx('ui-toggle', `ui-toggle--${tone}`, checked && 'ui-toggle--on', disabled && 'ui-toggle--disabled')}
      onClick={() => {
        if (disabled) return
        h.selection()
        onChange(!checked)
      }}
    >
      <motion.span
        className="ui-toggle-thumb"
        layout
        transition={{ type: 'spring', stiffness: 600, damping: 30 }}
      />
    </button>
  )
}
