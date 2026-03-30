"""
XShield — Traffic Charts Generator
Creates PNG charts for traffic visualization using matplotlib.
"""
import io
from datetime import datetime, timedelta, timezone
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter


def _format_bytes_axis(val, pos):
    """Format axis labels as human-readable bytes."""
    if val >= 1024 ** 3:
        return f"{val / (1024 ** 3):.1f} GB"
    elif val >= 1024 ** 2:
        return f"{val / (1024 ** 2):.0f} MB"
    elif val >= 1024:
        return f"{val / 1024:.0f} KB"
    return f"{val:.0f} B"


def _apply_style(fig, ax):
    """Apply dark theme styling."""
    bg_color = "#1a1a2e"
    text_color = "#e0e0e0"
    grid_color = "#2a2a4e"

    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.tick_params(colors=text_color)
    ax.xaxis.label.set_color(text_color)
    ax.yaxis.label.set_color(text_color)
    ax.title.set_color(text_color)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(grid_color)
    ax.spines["bottom"].set_color(grid_color)
    ax.grid(True, alpha=0.2, color=grid_color)


def generate_user_traffic_chart(
    user_name: str,
    upload_data: list[tuple[datetime, int]],
    download_data: list[tuple[datetime, int]],
) -> bytes:
    """
    Generate a traffic chart for a single user.
    Data format: list of (datetime, bytes) tuples.
    Returns PNG bytes.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_style(fig, ax)

    if upload_data:
        dates_up, values_up = zip(*upload_data)
        ax.fill_between(dates_up, values_up, alpha=0.3, color="#6c63ff", label="↑ Upload")
        ax.plot(dates_up, values_up, color="#6c63ff", linewidth=2)

    if download_data:
        dates_down, values_down = zip(*download_data)
        ax.fill_between(dates_down, values_down, alpha=0.3, color="#e94560", label="↓ Download")
        ax.plot(dates_down, values_down, color="#e94560", linewidth=2)

    ax.set_title(f"🛡️ XShield — {user_name}", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Дата")
    ax.set_ylabel("Трафик")
    ax.yaxis.set_major_formatter(FuncFormatter(_format_bytes_axis))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.legend(loc="upper left", framealpha=0.8)

    fig.autofmt_xdate()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_overview_chart(
    users: list[dict],
) -> bytes:
    """
    Generate overview bar chart of all users' traffic.
    users: list of {"name": str, "upload": int, "download": int}
    Returns PNG bytes.
    """
    fig, ax = plt.subplots(figsize=(10, max(4, len(users) * 0.6 + 1)))
    _apply_style(fig, ax)

    if not users:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                fontsize=16, color="#e0e0e0", transform=ax.transAxes)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    names = [u["name"] for u in users]
    uploads = [u["upload"] for u in users]
    downloads = [u["download"] for u in users]

    y_pos = range(len(names))
    bar_height = 0.35

    ax.barh([y - bar_height / 2 for y in y_pos], downloads,
            height=bar_height, color="#e94560", alpha=0.8, label="↓ Download")
    ax.barh([y + bar_height / 2 for y in y_pos], uploads,
            height=bar_height, color="#6c63ff", alpha=0.8, label="↑ Upload")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(names, fontsize=11)
    ax.xaxis.set_major_formatter(FuncFormatter(_format_bytes_axis))
    ax.set_title("🛡️ XShield — Трафик пользователей", fontsize=14,
                 fontweight="bold", pad=15)
    ax.legend(loc="lower right", framealpha=0.8)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def generate_server_load_chart(
    timestamps: list[datetime],
    cpu_values: list[float],
    ram_values: list[float],
) -> bytes:
    """
    Generate server load chart (CPU + RAM over time).
    Returns PNG bytes.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    _apply_style(fig, ax)

    if timestamps and cpu_values:
        ax.plot(timestamps, cpu_values, color="#ff6b6b", linewidth=2,
                label="CPU %", alpha=0.9)
    if timestamps and ram_values:
        ax.plot(timestamps, ram_values, color="#48c9b0", linewidth=2,
                label="RAM %", alpha=0.9)

    ax.set_ylim(0, 100)
    ax.set_title("🖥️ XShield — Нагрузка сервера", fontsize=14,
                 fontweight="bold", pad=15)
    ax.set_ylabel("Загрузка %")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.legend(loc="upper left", framealpha=0.8)

    fig.autofmt_xdate()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
