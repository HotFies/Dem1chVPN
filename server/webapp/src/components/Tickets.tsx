import React, { useState, useEffect, useCallback } from 'react'
import {
  Ticket, getMyTickets, getAllTickets, createTicket,
  replyToTicket, closeTicket,
} from '../api/client'

interface TicketsProps {
  isAdmin: boolean
}

type FilterTab = 'open' | 'closed' | 'all'

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
      {/* Header */}
      <div className="section-header">
        <h2>🎫 {isAdmin ? 'Тикеты' : 'Мои обращения'}</h2>
      </div>

      {/* Admin filter tabs */}
      {isAdmin && (
        <div className="filter-tabs">
          {(['open', 'closed', 'all'] as const).map(tab => (
            <button
              key={tab}
              className={`filter-tab ${filter === tab ? 'active' : ''}`}
              onClick={() => setFilter(tab)}
            >
              {{ open: '🔵 Открытые', closed: '✅ Закрытые', all: '📋 Все' }[tab]}
              {tab === 'open' && <span className="count">{openCount}</span>}
            </button>
          ))}
        </div>
      )}

      {/* Create ticket button (user) */}
      {!isAdmin && !showCreate && (
        <button
          className="btn-create-ticket"
          onClick={() => setShowCreate(true)}
        >
          ✏️ Новый тикет
        </button>
      )}

      {/* Create form */}
      {showCreate && (
        <div className="card ticket-create-form">
          <div className="card-header">✏️ Новый тикет</div>
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
              {sending ? '⏳ Отправка...' : '📨 Отправить'}
            </button>
            <button
              className="btn-sm btn-cancel"
              onClick={() => { setShowCreate(false); setNewMessage('') }}
            >
              ❌ Отмена
            </button>
          </div>
          <div className="ticket-char-count">
            {newMessage.length}/2000
          </div>
        </div>
      )}

      {/* Ticket list */}
      {loading ? (
        <div className="loading">⏳ Загрузка...</div>
      ) : tickets.length === 0 ? (
        <div className="empty-state">
          {isAdmin ? '✅ Нет тикетов' : '📭 У вас пока нет обращений'}
        </div>
      ) : (
        <div className="ticket-list">
          {tickets.map(ticket => (
            <div
              key={ticket.id}
              className={`ticket-card ${ticket.is_resolved ? 'resolved' : 'open'}`}
            >
              {/* Ticket header */}
              <div
                className="ticket-card-header"
                onClick={() => setExpandedId(expandedId === ticket.id ? null : ticket.id)}
              >
                <div className="ticket-meta">
                  <span className={`ticket-badge ${ticket.is_resolved ? 'badge-resolved' : 'badge-open'}`}>
                    {ticket.is_resolved ? '✅ Решён' : '🔵 Открыт'}
                  </span>
                  <span className="ticket-id">#{ticket.id}</span>
                  {isAdmin && ticket.user_name && (
                    <span className="ticket-author">👤 {ticket.user_name}</span>
                  )}
                </div>
                <span className="ticket-date">{formatDate(ticket.created_at)}</span>
              </div>

              {/* Ticket body — always show message preview, expand for full */}
              <div className={`ticket-body ${expandedId === ticket.id ? 'expanded' : ''}`}>
                <div className="ticket-message">
                  <span className="ticket-label">📝 Сообщение:</span>
                  <p>{ticket.message}</p>
                </div>

                {ticket.reply && (
                  <div className="ticket-reply">
                    <span className="ticket-label">💬 Ответ:</span>
                    <p>{ticket.reply}</p>
                  </div>
                )}

                {ticket.resolved_at && (
                  <div className="ticket-resolved-date">
                    ✅ Закрыт: {formatDate(ticket.resolved_at)}
                  </div>
                )}

                {/* Admin actions */}
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
                            {sending ? '⏳...' : '📨 Отправить ответ'}
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
                          💬 Ответить
                        </button>
                        <button
                          className="btn-sm btn-cancel"
                          onClick={() => handleClose(ticket.id)}
                        >
                          ✅ Закрыть
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
