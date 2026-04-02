import { useState, useEffect, useRef } from 'react';
import { getUsers, formatBytes, type User } from '../api/client';

interface TrafficChartProps {
  users?: User[];
}

const chartIcon = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10" />
    <line x1="12" y1="20" x2="12" y2="4" />
    <line x1="6" y1="20" x2="6" y2="14" />
  </svg>
);

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
    // Redraw on resize
    const handleResize = () => drawChart();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
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
    const padding = { top: 30, right: 16, bottom: 56, left: 52 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    ctx.clearRect(0, 0, width, height);

    const maxTraffic = Math.max(
      ...users.map((u) => Math.max(u.traffic_up, u.traffic_down)),
      1,
    );

    const barGroupWidth = chartW / users.length;
    const barWidth = Math.min(barGroupWidth * 0.35, 36);
    const gap = 3;

    // New color scheme matching design system
    const uploadColor = '#00d4ff';
    const downloadColor = '#7c3aed';
    const textColor = '#e8edf5';
    const hintColor = '#5a6d8f';
    const gridColor = 'rgba(255, 255, 255, 0.04)';

    // Grid lines
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    const gridLines = 4;
    for (let i = 0; i <= gridLines; i++) {
      const y = padding.top + (chartH / gridLines) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      const val = maxTraffic * (1 - i / gridLines);
      ctx.fillStyle = hintColor;
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.textAlign = 'right';
      ctx.fillText(formatBytes(val), padding.left - 8, y + 4);
    }

    // Bars
    users.forEach((user, idx) => {
      const x = padding.left + barGroupWidth * idx + barGroupWidth / 2;

      // Upload bar
      const upH = (user.traffic_up / maxTraffic) * chartH;
      const upX = x - barWidth - gap / 2;
      const upY = padding.top + chartH - upH;

      // Gradient for upload
      const upGrad = ctx.createLinearGradient(0, upY, 0, upY + upH);
      upGrad.addColorStop(0, uploadColor);
      upGrad.addColorStop(1, 'rgba(0, 212, 255, 0.3)');
      ctx.fillStyle = upGrad;
      roundedRect(ctx, upX, upY, barWidth, upH, 4);
      ctx.fill();

      // Download bar
      const downH = (user.traffic_down / maxTraffic) * chartH;
      const downX = x + gap / 2;
      const downY = padding.top + chartH - downH;

      const dnGrad = ctx.createLinearGradient(0, downY, 0, downY + downH);
      dnGrad.addColorStop(0, downloadColor);
      dnGrad.addColorStop(1, 'rgba(124, 58, 237, 0.3)');
      ctx.fillStyle = dnGrad;
      roundedRect(ctx, downX, downY, barWidth, downH, 4);
      ctx.fill();

      // User name label
      ctx.fillStyle = textColor;
      ctx.font = '11px "DM Sans", sans-serif';
      ctx.textAlign = 'center';
      ctx.save();
      ctx.translate(x, padding.top + chartH + 14);
      if (user.name.length > 8) {
        ctx.rotate(-Math.PI / 7);
      }
      ctx.fillText(
        user.name.length > 10 ? user.name.slice(0, 9) + '…' : user.name,
        0,
        0,
      );
      ctx.restore();
    });

    // Legend
    const legendY = 10;
    ctx.font = '11px "DM Sans", sans-serif';

    // Upload legend
    ctx.fillStyle = uploadColor;
    roundedRect(ctx, padding.left, legendY, 10, 10, 2);
    ctx.fill();
    ctx.fillStyle = textColor;
    ctx.textAlign = 'left';
    ctx.fillText('↑ Исходящий', padding.left + 14, legendY + 9);

    // Download legend
    ctx.fillStyle = downloadColor;
    roundedRect(ctx, padding.left + 100, legendY, 10, 10, 2);
    ctx.fill();
    ctx.fillStyle = textColor;
    ctx.fillText('↓ Входящий', padding.left + 114, legendY + 9);
  };

  if (loading) {
    return (
      <div className="loading-page">
        <div className="spinner" />
        <span>Загрузка графика...</span>
      </div>
    );
  }

  if (users.length === 0) {
    return <div className="chart-empty">Нет данных для графика</div>;
  }

  return (
    <div className="traffic-chart">
      <h3>{chartIcon} Трафик пользователей</h3>
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '260px' }}
      />
      <div className="chart-summary">
        <div className="stat">
          <span className="label">Всего ↑</span>
          <span className="value" style={{ color: '#00d4ff' }}>
            {formatBytes(users.reduce((s, u) => s + u.traffic_up, 0))}
          </span>
        </div>
        <div className="stat">
          <span className="label">Всего ↓</span>
          <span className="value" style={{ color: '#7c3aed' }}>
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
