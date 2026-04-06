import React, { useState, useCallback, useRef, useEffect } from 'react';

/* ── Хелпер для копирования ── */
function CopyBtn({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="guide-copy-row" onClick={copy}>
      <span className="guide-copy-label">{label}</span>
      <span className="guide-copy-value">{text}</span>
      <span className={`guide-copy-btn ${copied ? 'copied' : ''}`}>
        {copied ? '✓' : '📋'}
      </span>
    </div>
  );
}

/* ── Лайтбокс с поддержкой зума ── */
function Lightbox({ src, alt, onClose }: { src: string; alt: string; onClose: () => void }) {
  const imgRef = useRef<HTMLImageElement>(null);
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const lastDist = useRef<number | null>(null);
  const lastCenter = useRef<{ x: number; y: number } | null>(null);
  const isDragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const translateStart = useRef({ x: 0, y: 0 });

  const resetTransform = useCallback(() => {
    setScale(1);
    setTranslate({ x: 0, y: 0 });
  }, []);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  /* Зум по двойному тапу */
  const lastTap = useRef(0);
  const handleTap = () => {
    const now = Date.now();
    if (now - lastTap.current < 300) {
      if (scale > 1) {
        resetTransform();
      } else {
        setScale(2.5);
      }
    }
    lastTap.current = now;
  };

  /* Зум щипком (pinch) */
  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      lastDist.current = Math.hypot(dx, dy);
      lastCenter.current = {
        x: (e.touches[0].clientX + e.touches[1].clientX) / 2,
        y: (e.touches[0].clientY + e.touches[1].clientY) / 2,
      };
    } else if (e.touches.length === 1 && scale > 1) {
      isDragging.current = true;
      dragStart.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      translateStart.current = { ...translate };
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length === 2 && lastDist.current !== null) {
      e.preventDefault();
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      const dist = Math.hypot(dx, dy);
      const ratio = dist / lastDist.current;
      setScale((s: number) => Math.min(5, Math.max(1, s * ratio)));
      lastDist.current = dist;
    } else if (e.touches.length === 1 && isDragging.current && scale > 1) {
      const dx = e.touches[0].clientX - dragStart.current.x;
      const dy = e.touches[0].clientY - dragStart.current.y;
      setTranslate({
        x: translateStart.current.x + dx,
        y: translateStart.current.y + dy,
      });
    }
  };

  const handleTouchEnd = () => {
    lastDist.current = null;
    lastCenter.current = null;
    isDragging.current = false;
    if (scale <= 1) {
      resetTransform();
    }
  };

  /* Блокируем скролл страницы при открытом лайтбоксе */
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  return (
    <div className="guide-lightbox" onClick={handleBackdropClick}>
      <button className="guide-lightbox-close" onClick={onClose}>✕</button>
      <div className="guide-lightbox-hint">Двойной тап — приблизить/отдалить</div>
      <div
        className="guide-lightbox-img-wrap"
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onClick={handleTap}
      >
        <img
          ref={imgRef}
          src={src}
          alt={alt}
          className="guide-lightbox-img"
          style={{
            transform: `translate(${translate.x}px, ${translate.y}px) scale(${scale})`,
          }}
          draggable={false}
        />
      </div>
    </div>
  );
}

/* ── Миниатюра скриншота ── */
function Screenshot({ src, alt, onClick }: { src: string; alt: string; onClick: () => void }) {
  return (
    <div className="guide-screenshot" onClick={onClick}>
      <img src={src} alt={alt} loading="lazy" />
      <div className="guide-screenshot-zoom">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
          <line x1="11" y1="8" x2="11" y2="14" />
          <line x1="8" y1="11" x2="14" y2="11" />
        </svg>
      </div>
    </div>
  );
}

/* ── Базовый путь для ассетов (для поддержки Vite base) ── */
const BASE = import.meta.env.BASE_URL || '/webapp/';
const img = (name: string) => `${BASE}img/appstore-guide/${name}`;

/* ── Данные шагов ── */
const steps = [
  {
    num: 1,
    title: 'Перейдите в настройки аккаунта',
    desc: (
      <>
        Откройте <strong>Настройки</strong> → нажмите на <strong>ваше имя</strong> сверху →
        <strong> Контент и покупки</strong> → <strong>Просмотреть</strong>
      </>
    ),
    images: [
      { src: img('step1.webp'), alt: 'Настройки — ваше имя' },
      { src: img('step2.webp'), alt: 'Контент и покупки' },
      { src: img('step3.webp'), alt: 'Просмотреть аккаунт' },
    ],
  },
  {
    num: 2,
    title: 'Смените страну',
    desc: (
      <>
        Нажмите <strong>Страна или регион</strong> → выберите <strong>Соединённые Штаты (United States)</strong> → <strong>Продолжить</strong>
      </>
    ),
    images: [
      { src: img('step4.webp'), alt: 'Страна или регион' },
      { src: img('step5.webp'), alt: 'Выбор United States' },
      { src: img('step6.webp'), alt: 'Подтверждение смены' },
    ],
  },
  {
    num: 3,
    title: 'Примите условия',
    desc: (
      <>
        Нажмите <strong>«Принять» (Agree)</strong> в правом верхнем углу экрана
      </>
    ),
    images: [
      { src: img('step7.webp'), alt: 'Принять условия' },
    ],
  },
  {
    num: 4,
    title: 'Введите платёжные данные',
    desc: (
      <>
        В способе оплаты выберите <strong>«None» (Нет)</strong>. Затем заполните адрес — можно скопировать данные ниже:
      </>
    ),
    images: [
      { src: img('step8.webp'), alt: 'Форма оплаты и адреса' },
    ],
    copyData: [
      { label: '🏠 Адрес (Street)', value: '123 Main Street' },
      { label: '🏙️ Город (City)', value: 'New York' },
      { label: '📍 Штат (State)', value: 'New York' },
      { label: '📮 Индекс (ZIP)', value: '10001' },
      { label: '📞 Телефон (Phone)', value: '2120000000' },
    ],
  },
  {
    num: 5,
    title: 'Завершите настройку',
    desc: (
      <>
        Нажмите <strong>«Готово» (Done)</strong> в правом верхнем углу. Регион изменён!
      </>
    ),
    images: [
      { src: img('step9.webp'), alt: 'Готово — завершение' },
    ],
  },
];

/* ── Главный компонент гайда ── */
export default function AppStoreGuide({ onBack }: { onBack: () => void }) {
  const [lightboxSrc, setLightboxSrc] = useState<{ src: string; alt: string } | null>(null);

  return (
    <div className="guide-page">
      <button className="guide-back-btn" onClick={onBack}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="15 18 9 12 15 6" />
        </svg>
        Назад
      </button>

      <div className="guide-hero">
        <div className="guide-hero-icon">🍎</div>
        <h2 className="guide-hero-title">Смена региона App Store</h2>
        <p className="guide-hero-desc">
          Приложение V2RayTun удалено из российского App Store.
          Следуйте инструкции ниже, чтобы переключить регион на США, скачать приложение и вернуться обратно.
        </p>
      </div>

      <div className="guide-warning">
        <div className="guide-warning-icon">⚠️</div>
        <div className="guide-warning-text">
          <strong>Важно!</strong> Перед сменой региона отмените все активные подписки.
          <br />
          Проверьте: <strong>Настройки → Ваше имя → Подписки</strong>
        </div>
      </div>

      <div className="guide-steps">
        {steps.map((step) => (
          <div className="guide-step" key={step.num} style={{ animationDelay: `${step.num * 0.08}s` }}>
            <div className="guide-step-header">
              <div className="guide-step-num">{step.num}</div>
              <h3 className="guide-step-title">{step.title}</h3>
            </div>
            <p className="guide-step-desc">{step.desc}</p>

            <div className={`guide-screenshots ${step.images.length === 1 ? 'single' : ''}`}>
              {step.images.map((img, i) => (
                <Screenshot
                  key={i}
                  src={img.src}
                  alt={img.alt}
                  onClick={() => setLightboxSrc(img)}
                />
              ))}
            </div>

            {step.copyData && (
              <div className="guide-copy-block">
                {step.copyData.map((d, i) => (
                  <CopyBtn key={i} label={d.label} text={d.value} />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="guide-final">
        <div className="guide-final-icon">🔄</div>
        <div className="guide-final-text">
          <strong>После установки V2RayTun</strong> вы можете вернуть регион обратно на Россию, выполнив те же шаги и выбрав «Россия» в списке стран.
        </div>
      </div>

      {lightboxSrc && (
        <Lightbox
          src={lightboxSrc.src}
          alt={lightboxSrc.alt}
          onClose={() => setLightboxSrc(null)}
        />
      )}
    </div>
  );
}
