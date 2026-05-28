import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence, useMotionValue, useTransform } from 'framer-motion'
import {
  Apple,
  AlertTriangle,
  RefreshCcw,
  Home,
  Building,
  MapPin,
  Mailbox,
  Phone,
  ZoomIn,
  X,
} from 'lucide-react'
import { Sheet } from './ui/Sheet'
import { CopyButton } from './ui/CopyButton'
import { IconButton } from './ui/IconButton'

const BASE = (import.meta as any).env?.BASE_URL || '/webapp/'
const img = (name: string) => `${BASE}img/appstore-guide/${name}`

type ImgInfo = { src: string; alt: string }

const steps: Array<{
  num: number
  title: string
  desc: React.ReactNode
  images: ImgInfo[]
  copyData?: { label: string; value: string; icon: React.ReactNode }[]
}> = [
  {
    num: 1,
    title: 'Перейдите в настройки аккаунта',
    desc: <>Откройте <strong>Настройки</strong> → нажмите на <strong>ваше имя</strong> сверху → <strong>Контент и покупки</strong> → <strong>Просмотреть</strong></>,
    images: [
      { src: img('step1.webp'), alt: 'Настройки — ваше имя' },
      { src: img('step2.webp'), alt: 'Контент и покупки' },
      { src: img('step3.webp'), alt: 'Просмотреть аккаунт' },
    ],
  },
  {
    num: 2,
    title: 'Смените страну',
    desc: <>Нажмите <strong>Страна или регион</strong> → выберите <strong>Соединённые Штаты (United States)</strong> → <strong>Продолжить</strong></>,
    images: [
      { src: img('step4.webp'), alt: 'Страна или регион' },
      { src: img('step5.webp'), alt: 'Выбор United States' },
      { src: img('step6.webp'), alt: 'Подтверждение смены' },
    ],
  },
  {
    num: 3,
    title: 'Примите условия',
    desc: <>Нажмите <strong>«Принять» (Agree)</strong> в правом верхнем углу экрана</>,
    images: [{ src: img('step7.webp'), alt: 'Принять условия' }],
  },
  {
    num: 4,
    title: 'Введите платёжные данные',
    desc: <>В способе оплаты выберите <strong>«None» (Нет)</strong>. Затем заполните адрес — можно скопировать данные ниже:</>,
    images: [{ src: img('step8.webp'), alt: 'Форма оплаты и адреса' }],
    copyData: [
      { label: 'Адрес (Street)', value: '123 Main Street', icon: <Home size={14} /> },
      { label: 'Город (City)', value: 'New York', icon: <Building size={14} /> },
      { label: 'Штат (State)', value: 'New York', icon: <MapPin size={14} /> },
      { label: 'Индекс (ZIP)', value: '10001', icon: <Mailbox size={14} /> },
      { label: 'Телефон (Phone)', value: '2120000000', icon: <Phone size={14} /> },
    ],
  },
  {
    num: 5,
    title: 'Завершите настройку',
    desc: <>Нажмите <strong>«Готово» (Done)</strong> в правом верхнем углу. Регион изменён.</>,
    images: [{ src: img('step9.webp'), alt: 'Готово — завершение' }],
  },
]

function Lightbox({ src, alt, onClose }: { src: string; alt: string; onClose: () => void }) {
  const scale = useMotionValue(1)
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const opacity = useTransform(scale, [0.6, 1], [0, 1])
  const lastTap = useRef(0)
  const closeBtnRef = useRef<HTMLButtonElement | null>(null)
  const previousActive = useRef<Element | null>(null)

  useEffect(() => {
    previousActive.current = document.activeElement
    closeBtnRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      // фокус-trap: Tab закольцовывает на close-кнопку (единственный фокусируемый элемент)
      if (e.key === 'Tab') {
        e.preventDefault()
        closeBtnRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      ;(previousActive.current as HTMLElement | null)?.focus?.()
    }
  }, [onClose])

  const handleTap = () => {
    const now = Date.now()
    if (now - lastTap.current < 300) {
      const next = scale.get() > 1 ? 1 : 2.5
      scale.set(next)
      if (next === 1) { x.set(0); y.set(0) }
    }
    lastTap.current = now
  }

  return (
    <AnimatePresence>
      <motion.div
        className="guide-lightbox"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
        style={{ opacity }}
      >
        <div className="guide-lightbox-topbar">
          <IconButton ref={closeBtnRef} aria-label="Закрыть" onClick={onClose} variant="glass" size="md">
            <X size={20} />
          </IconButton>
        </div>
        <div className="guide-lightbox-hint">Двойной тап — приблизить</div>
        <motion.img
          src={src}
          alt={alt}
          className="guide-lightbox-img"
          drag
          dragConstraints={{ left: -200, right: 200, top: -200, bottom: 200 }}
          dragElastic={0.18}
          style={{ scale, x, y }}
          onClick={handleTap}
          draggable={false}
        />
      </motion.div>
    </AnimatePresence>
  )
}

function Screenshot({ src, alt, onClick }: { src: string; alt: string; onClick: () => void }) {
  return (
    <motion.button
      type="button"
      className="guide-screenshot"
      onClick={onClick}
      whileTap={{ scale: 0.97 }}
      transition={{ type: 'spring', stiffness: 380, damping: 28 }}
    >
      <img src={src} alt={alt} loading="lazy" />
      <span className="guide-screenshot-zoom">
        <ZoomIn size={18} strokeWidth={2} />
      </span>
    </motion.button>
  )
}

export default function AppStoreGuide({ onBack }: { onBack: () => void }) {
  const [lightboxSrc, setLightboxSrc] = useState<{ src: string; alt: string } | null>(null)

  return (
    <Sheet open onClose={onBack} title="Смена региона App Store" size="full" grabber={false} dismissible={false}>
      <div className="guide-content">
        <div className="guide-hero">
          <div className="guide-hero-icon"><Apple size={32} strokeWidth={1.5} /></div>
          <h2 className="guide-hero-title">Смена региона App Store</h2>
          <p className="guide-hero-desc">
            Приложение V2RayTun удалено из российского App Store.
            Следуйте инструкции ниже, чтобы переключить регион на США, скачать приложение и вернуться обратно.
          </p>
        </div>

        <div className="guide-warning">
          <div className="guide-warning-icon"><AlertTriangle size={20} strokeWidth={2} /></div>
          <div className="guide-warning-text">
            <strong>Важно.</strong> Перед сменой региона отмените все активные подписки.
            <br />
            Проверьте: <strong>Настройки → Ваше имя → Подписки</strong>
          </div>
        </div>

        <motion.div
          className="guide-steps"
          initial="hidden"
          animate="show"
          variants={{ hidden: {}, show: { transition: { staggerChildren: 0.06 } } }}
        >
          {steps.map(step => (
            <motion.div
              key={step.num}
              className="guide-step"
              variants={{ hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0 } }}
              transition={{ type: 'spring', stiffness: 260, damping: 24 }}
            >
              <div className="guide-step-header">
                <div className="guide-step-num">{step.num}</div>
                <h3 className="guide-step-title">{step.title}</h3>
              </div>
              <p className="guide-step-desc">{step.desc}</p>

              <div className={`guide-screenshots ${step.images.length === 1 ? 'single' : ''}`}>
                {step.images.map((image, i) => (
                  <Screenshot key={i} src={image.src} alt={image.alt} onClick={() => setLightboxSrc(image)} />
                ))}
              </div>

              {step.copyData && (
                <div className="guide-copy-block">
                  {step.copyData.map((d, i) => (
                    <div className="guide-copy-row" key={i}>
                      <span className="guide-copy-label">
                        {d.icon} {d.label}
                      </span>
                      <span className="guide-copy-value">{d.value}</span>
                      <CopyButton text={d.value} size="sm" />
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </motion.div>

        <div className="guide-final">
          <div className="guide-final-icon"><RefreshCcw size={20} strokeWidth={2} /></div>
          <div className="guide-final-text">
            <strong>После установки V2RayTun</strong> вы можете вернуть регион обратно на Россию,
            выполнив те же шаги и выбрав «Россия» в списке стран.
          </div>
        </div>
      </div>

      {lightboxSrc && (
        <Lightbox src={lightboxSrc.src} alt={lightboxSrc.alt} onClose={() => setLightboxSrc(null)} />
      )}
    </Sheet>
  )
}
