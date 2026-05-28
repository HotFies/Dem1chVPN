import React from 'react'
import clsx from 'clsx'

type Props = {
  width?: number | string
  height?: number | string
  radius?: 'sm' | 'md' | 'lg' | 'full'
  className?: string
  style?: React.CSSProperties
}

export function Skeleton({ width, height = 16, radius = 'md', className, style }: Props) {
  return (
    <span
      className={clsx('ui-skel', `ui-skel--r-${radius}`, className)}
      style={{ width: width ?? '100%', height, ...style }}
      aria-hidden
    />
  )
}

export function SkeletonStack({ rows = 3, gap = 10, height = 16 }: { rows?: number; gap?: number; height?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap }}>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} height={height} width={i === rows - 1 ? '60%' : '100%'} />
      ))}
    </div>
  )
}
