import React, { useState, useEffect } from 'react'
import { getUsers, formatBytes, type User } from '../api/client'

export default function UserList() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getUsers()
      .then(data => { setUsers(data.users || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">⏳ Загрузка...</div>

  return (
    <div className="user-list">
      <div className="section-header">
        <h2>👥 Пользователи ({users.length})</h2>
      </div>
      {users.length === 0 ? (
        <div className="empty-state">Нет пользователей</div>
      ) : (
        <div className="card-list">
          {users.map(u => (
            <div key={u.id} className={`user-card ${u.active ? '' : 'disabled'}`}>
              <div className="user-card-header">
                <span className="user-name">
                  {u.active ? '🟢' : '🔴'} {u.name}
                </span>
              </div>
              <div className="user-card-body">
                <div className="stat-row">
                  <span>Трафик</span>
                  <span>{formatBytes(u.traffic_total)} / {u.traffic_limit ? formatBytes(u.traffic_limit) : '♾️'}</span>
                </div>
                {u.traffic_limit && (
                  <div className="progress-bar">
                    <div className="progress-fill"
                         style={{
                           width: `${Math.min((u.traffic_total / u.traffic_limit) * 100, 100)}%`,
                           background: u.traffic_total > u.traffic_limit * 0.8 ? '#e94560' : '#6c63ff'
                         }} />
                  </div>
                )}
                <div className="stat-row">
                  <span>Срок</span>
                  <span>{u.expiry || '♾️ Бессрочно'}</span>
                </div>
              </div>
              <div className="user-card-actions">
                <button className="btn-sm">🔗 Ссылка</button>
                <button className="btn-sm">📱 QR</button>
                <button className="btn-sm">{u.active ? '⏸️' : '▶️'}</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
