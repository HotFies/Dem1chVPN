import React, { useState, useEffect, useCallback } from 'react'
import {
  Ticket, getMyTickets, getAllTickets, createTicket,
  replyToTicket, closeTicket,
} from '../api/client'

interface TicketsProps {
  isAdmin: boolean
}

type FilterTab = 'open' | 'closed' | 'all'


const ticketIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
)

const editIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
  </svg>
)

const sendIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
)

const userIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="12" height="12">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
)

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
      await loadTickets()
    } catch (err) {
      alert('Ошибка создания тикета')
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
      await loadTickets()
    } catch (err) {
      alert('Ошибка отправки ответа')
    }
    setSending(false)
  }

  const handleClose = async (ticketId: number) => {
    try {
      await closeTicket(ticketId)
      await loadTickets()
    } catch (err) {
      alert('Ошибка закрытия тикета')
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
        <div className="section-icon">{ticketIcon}</div>
        <h2>{isAdmin ? 'Тикеты' : 'Мои обращения'}</h2>
      </div>

      {isAdmin && (
        <div className="filter-tabs">
          {([
            { key: 'open' as const, label: 'Открытые', count: openCount },
            { key: 'closed' as const, label: 'Закрытые', count: null },
            { key: 'all' as const, label: 'Все', count: null },
          ]).map(tab => (
            <button
              key={tab.key}
              className={`filter-tab ${filter === tab.key ? 'active' : ''}`}
              onClick={() => setFilter(tab.key)}
            >
              {tab.label}
              {tab.count !== null && <span className="count">{tab.count}</span>}
            </button>
          ))}
        </div>
      )}

      {!isAdmin && !showCreate && (
        <button
          className="btn-create-ticket"
          onClick={() => setShowCreate(true)}
        >
          {editIcon}
          Новый тикет
        </button>
      )}

      {showCreate && (
        <div className="card ticket-create-form">
          <div className="card-header">
            {editIcon}
            <span style={{ marginLeft: 8, flex: 1 }}>Новый тикет</span>
          </div>
          <textarea
            className="ticket-textarea"
            placeholder="Опишите вашу проблему или вопрос..."
            value={newMessage}
            onChange={e => setNewMessage(e.target.value)}
            rows={4}
            maxLength={2000}
          />
          <div className="ticket-form-actions">
            <button
              className="btn-sm btn-send"
              onClick={handleCreate}
              disabled={sending || newMessage.length < 5}
            >
              {sending ? (
                <><div className="spinner" style={{ width: 14, height: 14 }} /> Отправка...</>
              ) : (
                <>{sendIcon} Отправить</>
              )}
            </button>
            <button
              className="btn-sm btn-cancel"
              onClick={() => { setShowCreate(false); setNewMessage('') }}
            >
              Отмена
            </button>
          </div>
          <div className="ticket-char-count">
            {newMessage.length}/2000
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading-page">
          <div className="spinner" />
          <span>Загрузка тикетов...</span>
        </div>
      ) : tickets.length === 0 ? (
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="48" height="48" style={{ margin: '0 auto 12px', display: 'block', opacity: 0.3 }}>
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          {isAdmin ? 'Нет тикетов' : 'У вас пока нет обращений'}
        </div>
      ) : (
        <div className="ticket-list">
          {tickets.map((ticket, i) => (
            <div
              key={ticket.id}
              className={`ticket-card ${ticket.is_resolved ? 'resolved' : 'open'}`}
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div
                className="ticket-card-header"
                onClick={() => setExpandedId(expandedId === ticket.id ? null : ticket.id)}
              >
                <div className="ticket-meta">
                  <span className={`ticket-badge ${ticket.is_resolved ? 'badge-resolved' : 'badge-open'}`}>
                    {ticket.is_resolved ? '✓ Решён' : 'Открыт'}
                  </span>
                  <span className="ticket-id">#{ticket.id}</span>
                  {isAdmin && ticket.user_name && (
                    <span className="ticket-author">
                      {userIcon} {ticket.user_name}
                    </span>
                  )}
                </div>
                <span className="ticket-date">{formatDate(ticket.created_at)}</span>
              </div>

              <div className={`ticket-body ${expandedId === ticket.id ? 'expanded' : ''}`}>
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
                    ✓ Закрыт: {formatDate(ticket.resolved_at)}
                  </div>
                )}

                {isAdmin && !ticket.is_resolved && expandedId === ticket.id && (
                  <div className="ticket-actions">
                    {replyTicketId === ticket.id ? (
                      <div className="reply-form">
                        <textarea
                          className="ticket-textarea"
                          placeholder="Введите ответ..."
                          value={replyText}
                          onChange={e => setReplyText(e.target.value)}
                          rows={3}
                        />
                        <div className="ticket-form-actions">
                          <button
                            className="btn-sm btn-send"
                            onClick={() => handleReply(ticket.id)}
                            disabled={sending || !replyText.trim()}
                          >
                            {sending ? (
                              <><div className="spinner" style={{ width: 14, height: 14 }} /> Отправка...</>
                            ) : (
                              <>{sendIcon} Ответить</>
                            )}
                          </button>
                          <button
                            className="btn-sm btn-cancel"
                            onClick={() => { setReplyTicketId(null); setReplyText('') }}
                          >
                            Отмена
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="ticket-form-actions">
                        <button
                          className="btn-sm btn-send"
                          onClick={() => setReplyTicketId(ticket.id)}
                        >
                          {sendIcon} Ответить
                        </button>
                        <button
                          className="btn-sm btn-cancel"
                          onClick={() => handleClose(ticket.id)}
                        >
                          ✓ Закрыть
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
