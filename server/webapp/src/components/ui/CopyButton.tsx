import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, Copy } from 'lucide-react'
import clsx from 'clsx'
import { useHaptic } from '../../hooks/useHaptic'
import { useToast } from '../../hooks/useToast'

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    try {
      const ok = document.execCommand('copy')
      document.body.removeChild(ta)
      return ok
    } catch {
      document.body.removeChild(ta)
      return false
    }
  }
}

type Props = {
  text: string
  label?: string
  size?: 'sm' | 'md'
  variant?: 'plain' | 'pill'
  toastMessage?: string | null
  className?: string
}

export function CopyButton({ text, label, size = 'md', variant = 'plain', toastMessage = 'Скопировано', className }: Props) {
  const [copied, setCopied] = useState(false)
  const h = useHaptic()
  const toast = useToast()

  const handle = async () => {
    const ok = await copyToClipboard(text)
    if (ok) {
      setCopied(true)
      h.notify('success')
      if (toastMessage) toast.success(toastMessage, 1800)
      setTimeout(() => setCopied(false), 1800)
    } else {
      toast.error('Не удалось скопировать')
      h.notify('error')
    }
  }

  const iconSize = size === 'sm' ? 14 : 16

  return (
    <motion.button
      type="button"
      onClick={handle}
      whileTap={{ scale: 0.92 }}
      transition={{ type: 'spring', stiffness: 400, damping: 28 }}
      className={clsx('ui-copy', `ui-copy--${variant}`, `ui-copy--${size}`, copied && 'ui-copy--copied', className)}
      aria-label={copied ? 'Скопировано' : 'Копировать'}
    >
      <AnimatePresence mode="wait" initial={false}>
        {copied ? (
          <motion.span
            key="check"
            initial={{ scale: 0.5, opacity: 0, rotate: -20 }}
            animate={{ scale: 1, opacity: 1, rotate: 0 }}
            exit={{ scale: 0.5, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 400, damping: 18 }}
            className="ui-copy-ico"
          >
            <Check size={iconSize} />
          </motion.span>
        ) : (
          <motion.span
            key="copy"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ duration: 0.12 }}
            className="ui-copy-ico"
          >
            <Copy size={iconSize} strokeWidth={1.75} />
          </motion.span>
        )}
      </AnimatePresence>
      {label && <span className="ui-copy-label">{copied ? 'Готово' : label}</span>}
    </motion.button>
  )
}
