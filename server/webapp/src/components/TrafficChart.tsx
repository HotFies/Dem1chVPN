import { useState, useEffect, useRef } from 'react';
import { getUsers, formatBytes, type User } from '../api/client';

interface TrafficChartProps {
  users?: User[];
}

/**
 * TrafficChart — Canvas-based traffic visualization
 * Shows bar chart of upload/download per user
 */
export default function TrafficChart({ users: propUsers }: TrafficChartProps) {
  const [users, setUsers] = useState<User[]>(propUsers || []);
  const [loading, setLoading] = useState(!propUsers);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!propUsers) {
      getUsers()
        .then((data) => setUsers(data.users))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [propUsers]);

  useEffect(() => {
    if (users.length === 0) return;
    drawChart();
  }, [users]);

  const drawChart = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const padding = { top: 30, right: 20, bottom: 60, left: 60 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    // Clear
    ctx.clearRect(0, 0, width, height);

    // Find max traffic
    const maxTraffic = Math.max(
      ...users.map((u) => Math.max(u.traffic_up, u.traffic_down)),
      1,
    );

    const barGroupWidth = chartW / users.length;
    const barWidth = Math.min(barGroupWidth * 0.35, 40);
    const gap = 4;

    // Colors
    const uploadColor = '#6366f1';
    const downloadColor = '#06b6d4';
    const textColor = getComputedStyle(document.documentElement)
      .getPropertyValue('--tg-theme-text-color')
      .trim() || '#e2e8f0';
    const hintColor = getComputedStyle(document.documentElement)
      .getPropertyValue('--tg-theme-hint-color')
      .trim() || '#94a3b8';
    const gridColor = 'rgba(148,163,184,0.15)';

    // Draw grid lines
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    const gridLines = 5;
    for (let i = 0; i <= gridLines; i++) {
      const y = padding.top + (chartH / gridLines) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      // Y-axis labels
      const val = maxTraffic * (1 - i / gridLines);
      ctx.fillStyle = hintColor;
      ctx.font = '11px -apple-system, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(formatBytes(val), padding.left - 8, y + 4);
    }

    // Draw bars
    users.forEach((user, idx) => {
      const x = padding.left + barGroupWidth * idx + barGroupWidth / 2;

      // Upload bar
      const upH = (user.traffic_up / maxTraffic) * chartH;
      const upX = x - barWidth - gap / 2;
      const upY = padding.top + chartH - upH;

      ctx.fillStyle = uploadColor;
      roundedRect(ctx, upX, upY, barWidth, upH, 4);
      ctx.fill();

      // Download bar
      const downH = (user.traffic_down / maxTraffic) * chartH;
      const downX = x + gap / 2;
      const downY = padding.top + chartH - downH;

      ctx.fillStyle = downloadColor;
      roundedRect(ctx, downX, downY, barWidth, downH, 4);
      ctx.fill();

      // User name label
      ctx.fillStyle = textColor;
      ctx.font = '12px -apple-system, sans-serif';
      ctx.textAlign = 'center';
      ctx.save();
      ctx.translate(x, padding.top + chartH + 14);
      if (user.name.length > 8) {
        ctx.rotate(-Math.PI / 6);
      }
      ctx.fillText(
        user.name.length > 12 ? user.name.slice(0, 11) + '…' : user.name,
        0,
        0,
      );
      ctx.restore();
    });

    // Legend
    const legendY = 12;
    ctx.font = '12px -apple-system, sans-serif';

    ctx.fillStyle = uploadColor;
    ctx.fillRect(padding.left, legendY, 12, 12);
    ctx.fillStyle = textColor;
    ctx.textAlign = 'left';
    ctx.fillText('↑ Upload', padding.left + 16, legendY + 10);

    ctx.fillStyle = downloadColor;
    ctx.fillRect(padding.left + 100, legendY, 12, 12);
    ctx.fillStyle = textColor;
    ctx.fillText('↓ Download', padding.left + 116, legendY + 10);
  };

  if (loading) {
    return <div className="chart-loading">Загрузка графика...</div>;
  }

  if (users.length === 0) {
    return <div className="chart-empty">Нет данных для графика</div>;
  }

  return (
    <div className="traffic-chart">
      <h3>📊 Трафик пользователей</h3>
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '280px' }}
      />
      <div className="chart-summary">
        <div className="stat">
          <span className="label">Всего ↑</span>
          <span className="value">
            {formatBytes(users.reduce((s, u) => s + u.traffic_up, 0))}
          </span>
        </div>
        <div className="stat">
          <span className="label">Всего ↓</span>
          <span className="value">
            {formatBytes(users.reduce((s, u) => s + u.traffic_down, 0))}
          </span>
        </div>
      </div>
    </div>
  );
}

function roundedRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  if (h <= 0) return;
  r = Math.min(r, h / 2, w / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.arcTo(x + w, y, x + w, y + r, r);
  ctx.lineTo(x + w, y + h);
  ctx.lineTo(x, y + h);
  ctx.lineTo(x, y + r);
  ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
}
