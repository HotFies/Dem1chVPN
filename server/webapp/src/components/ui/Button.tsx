import React, { forwardRef } from 'react'
import { motion, MotionProps } from 'framer-motion'
import clsx from 'clsx'
import { Loader2 } from 'lucide-react'
import { useHaptic } from '../../hooks/useHaptic'

type Variant = 'primary' | 'ghost' | 'subtle' | 'success' | 'danger'
type Size = 'sm' | 'md' | 'lg'

type ButtonProps = {
  variant?: Variant
  size?: Size
  loading?: boolean
  disabled?: boolean
  fullWidth?: boolean
  haptic?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  children?: React.ReactNode
  className?: string
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void
  type?: 'button' | 'submit' | 'reset'
  'aria-label'?: string
} & Pick<MotionProps, 'whileTap'>

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = 'primary',
    size = 'md',
    loading,
    disabled,
    fullWidth,
    haptic = true,
    leftIcon,
    rightIcon,
    children,
    className,
    onClick,
    type = 'button',
    ...rest
  },
  ref
) {
  const h = useHaptic()
  const isDisabled = disabled || loading

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (isDisabled) return
    if (haptic) h.impact('light')
    onClick?.(e)
  }

  return (
    <motion.button
      ref={ref}
      type={type}
      onClick={handleClick}
      disabled={isDisabled}
      whileTap={isDisabled ? undefined : { scale: 0.97 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className={clsx(
        'ui-btn',
        `ui-btn--${variant}`,
        `ui-btn--${size}`,
        fullWidth && 'ui-btn--full',
        loading && 'ui-btn--loading',
        className
      )}
      {...rest}
    >
      {loading ? (
        <Loader2 size={size === 'sm' ? 14 : 16} className="ui-btn-spin" />
      ) : (
        leftIcon
      )}
      {children && <span className="ui-btn-label">{children}</span>}
      {!loading && rightIcon}
    </motion.button>
  )
})
