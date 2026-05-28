import React from 'react'
import { LucideIcon } from 'lucide-react'

type IconProps = {
  icon: LucideIcon
  size?: number
  strokeWidth?: number
  className?: string
  'aria-hidden'?: boolean
  'aria-label'?: string
}

export function Icon({ icon: I, size = 20, strokeWidth = 1.75, className, ...rest }: IconProps) {
  return <I size={size} strokeWidth={strokeWidth} className={className} aria-hidden={rest['aria-label'] ? undefined : true} {...rest} />
}
