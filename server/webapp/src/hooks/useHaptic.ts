import { getTelegram } from './useTelegram'

type Impact = 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'
type Notification = 'success' | 'warning' | 'error'

export function useHaptic() {
  return {
    impact(style: Impact = 'light') {
      try { getTelegram()?.HapticFeedback?.impactOccurred(style) } catch {}
    },
    notify(type: Notification) {
      try { getTelegram()?.HapticFeedback?.notificationOccurred(type) } catch {}
    },
    selection() {
      try { getTelegram()?.HapticFeedback?.selectionChanged() } catch {}
    },
  }
}
