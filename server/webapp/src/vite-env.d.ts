/// <reference types="vite/client" />

interface Window {
  Telegram?: {
    WebApp: {
      ready(): void
      expand(): void
      close(): void
      enableClosingConfirmation(): void
      initData: string
      initDataUnsafe: {
        user?: {
          id: number
          first_name: string
          last_name?: string
          username?: string
          language_code?: string
        }
      }
      themeParams: {
        bg_color?: string
        text_color?: string
        hint_color?: string
        link_color?: string
        button_color?: string
        button_text_color?: string
        secondary_bg_color?: string
        header_bg_color?: string
      }
      colorScheme: 'light' | 'dark'
      MainButton: {
        text: string
        color: string
        textColor: string
        isVisible: boolean
        isActive: boolean
        show(): void
        hide(): void
        onClick(fn: () => void): void
        offClick(fn: () => void): void
        setText(text: string): void
      }
      BackButton: {
        isVisible: boolean
        show(): void
        hide(): void
        onClick(fn: () => void): void
        offClick(fn: () => void): void
      }
    }
  }
}
