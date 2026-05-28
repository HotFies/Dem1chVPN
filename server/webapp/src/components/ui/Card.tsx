import React, { forwardRef } from 'react'
import { motion, MotionProps } from 'framer-motion'
import clsx from 'clsx'

type Props = {
  children: React.ReactNode
  padding?: 'sm' | 'md' | 'lg'
  interactive?: boolean
  className?: string
  onClick?: () => void
  as?: 'div' | 'section' | 'article'
  delay?: number
} & Pick<MotionProps, 'layout' | 'layoutId' | 'initial' | 'animate' | 'exit'>

export const Card = forwardRef<HTMLDivElement, Props>(function Card(
  { children, padding = 'md', interactive, className, onClick, as = 'div', delay = 0, layout, layoutId, initial, animate, exit },
  ref
) {
  const Motion = motion[as] as typeof motion.div
  return (
    <Motion
      ref={ref}
      onClick={onClick}
      layout={layout}
      layoutId={layoutId}
      initial={initial ?? { opacity: 0, y: 12 }}
      animate={animate ?? { opacity: 1, y: 0 }}
      exit={exit}
      transition={{ type: 'spring', stiffness: 260, damping: 26, delay }}
      whileTap={interactive ? { scale: 0.99 } : undefined}
      className={clsx('ui-card', `ui-card--p-${padding}`, interactive && 'ui-card--interactive', className)}
    >
      {children}
    </Motion>
  )
})

export function CardHeader({ icon, title, action }: { icon?: React.ReactNode; title: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="ui-card-head">
      {icon && <span className="ui-card-head-ico">{icon}</span>}
      <span className="ui-card-head-title">{title}</span>
      {action && <span className="ui-card-head-action">{action}</span>}
    </div>
  )
}
