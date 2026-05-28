import React from 'react'
import { Skeleton } from './ui/Skeleton'

export function AuthSkeleton() {
  return (
    <div className="auth-skel">
      <Skeleton height={28} width={160} radius="md" />
      <div style={{ height: 16 }} />
      <Skeleton height={120} radius="lg" />
      <div style={{ height: 10 }} />
      <Skeleton height={80} radius="lg" />
      <div style={{ height: 10 }} />
      <Skeleton height={80} radius="lg" />
    </div>
  )
}
