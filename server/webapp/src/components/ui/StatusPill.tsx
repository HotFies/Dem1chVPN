import React from 'react'
import clsx from 'clsx'

type Tone = 'active' | 'inactive' | 'expired' | 'warning' | 'neutral'

const LABEL: Record<Tone, string> = {
  active: 'Активен',
  inactive: 'Отключён',
  expired: 'Истёк',
  warning: 'Внимание',
  neutral: '—',
}

export function StatusPill({ tone, children, pulse = true }: { tone: Tone; children?: React.ReactNode; pulse?: boolean }) {
  return (
    <span className={clsx('ui-pill', `ui-pill--${tone}`)}>
      <span className={clsx('ui-pill-dot', pulse && tone === 'active' && 'ui-pill-dot--pulse')} />
      {children ?? LABEL[tone]}
    </span>
  )
}
