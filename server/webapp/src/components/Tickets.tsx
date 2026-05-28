import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageSquare,
  Plus,
  Send,
  Check,
  X as XIcon,
  User as UserIcon,
} from 'lucide-react'
import {
  Ticket, getMyTickets, getAllTickets, createTicket,
  replyToTicket, closeTicket,
} from '../api/client'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { Button } from './ui/Button'
import { Tabs } from './ui/Tabs'
import { Skeleton } from './ui/Skeleton'

interface TicketsProps { isAdmin: boolean }
type FilterTab = 'open' | 'closed' | 'all'

const MAX_LEN = 2000

function CircularCounter({ value, max = MAX_LEN, size = 22 }: { value: number; max?: number; size?: number }) {
  const r = (size - 4) / 2
  const c = 2 * Math.PI * r
  const pct = Math.min(value / max, 1)
  const offset = c - pct * c
  const danger = pct >= 0.9
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={2} />
      <circle
        cx={size / 2} cy={size / 2} r={r}
        fill="none"
        stroke={danger ? 'var(--danger)' : 'var(--accent)'}
        strokeWidth={2}
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: 'stroke-dashoffset 0.2s linear, stroke 0.2s' }}
      />
    </svg>
  )
}

export default function Tickets({ isAdmin }: TicketsProps) {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<FilterTab>('open')
  const [showCreate, setShowCreate] = useState(false)
  const [newMessage, setNewMessage] = useState('')
  const [replyTicketId, setReplyTicketId] = useState<number | null>(null)
  const [replyText, setReplyText] = useState('')
  const [sending, setSending] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const toast = useToast()
  const confirm = useConfirm()

  const loadTickets = useCallback(async () => {
    setLoading(true)
    try {
      if (isAdmin) {
        const data = await getAllTickets(filter)
        setTickets(data.tickets)
      } else {
        const data = await getMyTickets()
        setTickets(data.tickets)
      }
    } catch (err) {
      console.error('Failed to load tickets:', err)
    }
    setLoading(false)
  }, [isAdmin, filter])

  useEffect(() => { loadTickets() }, [loadTickets])

  const handleCreate = async () => {
    if (!newMessage.trim() || newMessage.length < 5) return
    setSending(true)
    try {
      await createTicket(newMessage)
      setNewMessage('')
      setShowCreate(false)
      toast.success('Тикет создан')
      await loadTickets()
    } catch {
      toast.error('Не удалось создать тикет')
    }
    setSending(false)
  }

  const handleReply = async (ticketId: number) => {
    if (!replyText.trim()) return
    setSending(true)
    try {
      await replyToTicket(ticketId, replyText)
      setReplyTicketId(null)
      setReplyText('')
      toast.success('Ответ отправлен')
      await loadTickets()
    } catch {
      toast.error('Не удалось отправить ответ')
    }
    setSending(false)
  }

  const handleClose = async (ticketId: number) => {
    const ok = await confirm({
      title: 'Закрыть тикет?',
      description: 'Пользователь больше не сможет писать в этот тикет.',
      confirmLabel: 'Закрыть',
      destructive: true,
    })
    if (!ok) return
    try {
      await closeTicket(ticketId)
      toast.success('Тикет закрыт')
      await loadTickets()
    } catch {
      toast.error('Не удалось закрыть тикет')
    }
  }

  const formatDate = (iso: string | null) => {
    if (!iso) return '—'
    const d = new Date(iso)
    return d.toLocaleDateString('ru-RU', {
      day: '2-digit', month: '2-digit', year: '2-digit',
      hour: '2-digit', minute: '2-digit',
    })
  }

  const openCount = tickets.filter(t => !t.is_resolved).length

  return (
    <div className="tickets-page">
      <div className="section-header">
        <div className="section-icon">
          <MessageSquare size={22} strokeWidth={1.75} />
        </div>
        <h2>{isAdmin ? 'Тикеты' : 'Мои обращения'}</h2>
      </div>

      {isAdmin && (
        <div style={{ marginBottom: 12 }}>
          <Tabs<FilterTab>
            items={[
              { key: 'open', label: 'Открытые', count: openCount },
              { key: 'closed', label: 'Закрытые' },
              { key: 'all', label: 'Все' },
            ]}
            value={filter}
            onChange={setFilter}
            layoutId="tickets-tabs"
          />
        </div>
      )}

      {!isAdmin && !showCreate && (
        <Button variant="primary" size="lg" fullWidth leftIcon={<Plus size={18} />} onClick={() => setShowCreate(true)}>
          Новый тикет
        </Button>
      )}

      <AnimatePresence initial={false}>
        {showCreate && (
          <motion.div
            key="create"
            initial={{ opacity: 0, y: -8, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -6, height: 0 }}
            transition={{ type: 'spring', stiffness: 280, damping: 28 }}
            style={{ overflow: 'hidden' }}
          >
            <div className="card ticket-create-form" style={{ marginTop: 12 }}>
              <div className="card-header" style={{ gap: 8 }}>
                <Plus size={18} strokeWidth={2} color="var(--accent)" />
                <span style={{ flex: 1 }}>Новый тикет</span>
              </div>
              <label htmlFor="ticket-new" className="sr-only">Текст обращения</label>
              <textarea
                id="ticket-new"
                autoFocus
                className="ticket-textarea"
                placeholder="Опишите вашу проблему или вопрос..."
                value={newMessage}
                onChange={e => setNewMessage(e.target.value.slice(0, MAX_LEN))}
                rows={4}
                maxLength={MAX_LEN}
                aria-describedby="ticket-new-counter"
              />
              <div className="ticket-form-actions" style={{ alignItems: 'center' }}>
                <Button
                  size="sm" variant="success"
                  loading={sending}
                  disabled={newMessage.length < 5}
                  leftIcon={!sending ? <Send size={14} /> : undefined}
                  onClick={handleCreate}
                >
                  {sending ? 'Отправка' : 'Отправить'}
                </Button>
                <Button
                  size="sm" variant="ghost"
                  onClick={() => { setShowCreate(false); setNewMessage('') }}
                  leftIcon={<XIcon size={14} />}
                >
                  Отмена
                </Button>
                <div style={{ flex: 1 }} />
                <div className="ticket-counter" id="ticket-new-counter">
                  <CircularCounter value={newMessage.length} />
                  <span className="num">{newMessage.length}/{MAX_LEN}</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 12 }}>
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} height={72} radius="lg" />
          ))}
        </div>
      ) : tickets.length === 0 ? (
        <div className="empty-state">
          <MessageSquare size={48} strokeWidth={1.5} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.3 }} />
          {isAdmin ? 'Нет тикетов' : 'У вас пока нет обращений'}
        </div>
      ) : (
        <motion.ul className="ticket-list" layout style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          <AnimatePresence initial={false}>
            {tickets.map(ticket => (
              <motion.li
                key={ticket.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.16 } }}
                transition={{ type: 'spring', stiffness: 280, damping: 26 }}
                className={`ticket-card ${ticket.is_resolved ? 'resolved' : 'open'}`}
              >
                <button
                  type="button"
                  className="ticket-card-header"
                  onClick={() => setExpandedId(expandedId === ticket.id ? null : ticket.id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', width: '100%', display: 'flex', justifyContent: 'space-between' }}
                >
                  <div className="ticket-meta">
                    <span className={`ticket-badge ${ticket.is_resolved ? 'badge-resolved' : 'badge-open'}`}>
                      {ticket.is_resolved ? (
                        <><Check size={11} strokeWidth={3} /> Решён</>
                      ) : 'Открыт'}
                    </span>
                    <span className="ticket-id num">#{ticket.id}</span>
                    {isAdmin && ticket.user_name && (
                      <span className="ticket-author">
                        <UserIcon size={12} strokeWidth={2} /> {ticket.user_name}
                      </span>
                    )}
                  </div>
                  <span className="ticket-date num">{formatDate(ticket.created_at)}</span>
                </button>

                <AnimatePresence initial={false}>
                  {expandedId === ticket.id && (
                    <motion.div
                      key="body"
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ type: 'spring', stiffness: 260, damping: 28 }}
                      style={{ overflow: 'hidden' }}
                    >
                      <div className="ticket-body expanded">
                        <div className="ticket-message">
                          <span className="ticket-label">Сообщение</span>
                          <p>{ticket.message}</p>
                        </div>

                        {ticket.reply && (
                          <div className="ticket-reply">
                            <span className="ticket-label">Ответ</span>
                            <p>{ticket.reply}</p>
                          </div>
                        )}

                        {ticket.resolved_at && (
                          <div className="ticket-resolved-date">
                            <Check size={11} strokeWidth={2.5} /> Закрыт: {formatDate(ticket.resolved_at)}
                          </div>
                        )}

                        {isAdmin && !ticket.is_resolved && (
                          <div className="ticket-actions">
                            {replyTicketId === ticket.id ? (
                              <div className="reply-form">
                                <textarea
                                  autoFocus
                                  className="ticket-textarea"
                                  placeholder="Введите ответ..."
                                  value={replyText}
                                  onChange={e => setReplyText(e.target.value)}
                                  rows={3}
                                />
                                <div className="ticket-form-actions">
                                  <Button
                                    size="sm" variant="success" loading={sending}
                                    leftIcon={!sending ? <Send size={14} /> : undefined}
                                    disabled={!replyText.trim()}
                                    onClick={() => handleReply(ticket.id)}
                                  >
                                    {sending ? 'Отправка' : 'Ответить'}
                                  </Button>
                                  <Button size="sm" variant="ghost" leftIcon={<XIcon size={14} />} onClick={() => { setReplyTicketId(null); setReplyText('') }}>
                                    Отмена
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <div className="ticket-form-actions">
                                <Button size="sm" variant="primary" leftIcon={<Send size={14} />} onClick={() => setReplyTicketId(ticket.id)}>
                                  Ответить
                                </Button>
                                <Button size="sm" variant="ghost" leftIcon={<Check size={14} />} onClick={() => handleClose(ticket.id)}>
                                  Закрыть
                                </Button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.li>
            ))}
          </AnimatePresence>
        </motion.ul>
      )}
    </div>
  )
}
