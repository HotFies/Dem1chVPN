import React, { forwardRef } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'
import { useHaptic } from '../../hooks/useHaptic'

type Props = {
  children: React.ReactNode
  onClick?: () => void
  'aria-label': string
  variant?: 'plain' | 'glass' | 'accent' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  haptic?: boolean
  className?: string
}

export const IconButton = forwardRef<HTMLButtonElement, Props>(function IconButton(
  { children, onClick, variant = 'plain', size = 'md', disabled, haptic = true, className, ...rest },
  ref
) {
  const h = useHaptic()
  return (
    <motion.button
      ref={ref}
      type="button"
      onClick={() => {
        if (disabled) return
        if (haptic) h.impact('light')
        onClick?.()
      }}
      disabled={disabled}
      whileTap={disabled ? undefined : { scale: 0.9 }}
      transition={{ type: 'spring', stiffness: 400, damping: 28 }}
      className={clsx('ui-icon-btn', `ui-icon-btn--${variant}`, `ui-icon-btn--${size}`, className)}
      {...rest}
    >
      {children}
    </motion.button>
  )
})
