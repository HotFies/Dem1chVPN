import React from 'react'
import { Loader2 } from 'lucide-react'
import clsx from 'clsx'

type Props = {
  size?: 'xs' | 'sm' | 'md' | 'lg'
  tone?: 'accent' | 'muted'
  className?: string
}

const SIZE: Record<NonNullable<Props['size']>, number> = { xs: 12, sm: 16, md: 20, lg: 32 }

export function Spinner({ size = 'md', tone = 'accent', className }: Props) {
  return <Loader2 size={SIZE[size]} className={clsx('ui-spin', `ui-spin--${tone}`, className)} aria-hidden />
}
