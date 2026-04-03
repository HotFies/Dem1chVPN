"""
Dem1chVPN — Traffic Charts Generator
Creates PNG charts for traffic visualization using matplotlib.
Premium dark theme with gradient bars and smooth curves.
"""
import io
from datetime import datetime, timedelta, timezone
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np


# ── Color Palette (matches Mini App) ──
BG_DEEP = "#050a18"
BG_CARD = "#0c1428"
TEXT_PRIMARY = "#e8edf5"
TEXT_SECONDARY = "#8899b8"
TEXT_TERTIARY = "#5a6d8f"
GRID_COLOR = "#162040"
CYAN = "#00d4ff"
VIOLET = "#7c3aed"
EMERALD = "#10b981"
CORAL = "#ff4757"
CYAN_SOFT = "#4dd8ff"
VIOLET_SOFT = "#a78bfa"


def _format_bytes_axis(val, pos):
    """Format axis labels as human-readable bytes."""
    if val >= 1024 ** 3:
        return f"{val / (1024 ** 3):.1f} GB"
    elif val >= 1024 ** 2:
        return f"{val / (1024 ** 2):.0f} MB"
    elif val >= 1024:
        return f"{val / 1024:.0f} KB"
    return f"{val:.0f} B"


def _format_bytes_short(val):
    """Format bytes as short string."""
    if val >= 1024 ** 3:
        return f"{val / (1024 ** 3):.1f} GB"
    elif val >= 1024 ** 2:
        return f"{val / (1024 ** 2):.1f} MB"
    elif val >= 1024:
        return f"{val / 1024:.0f} KB"
    return f"{val:.0f} B"


def _apply_style(fig, ax):
    """Apply premium dark theme styling."""
    fig.patch.set_facecolor(BG_DEEP)
    ax.set_facecolor(BG_CARD)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.xaxis.label.set_color(TEXT_SECONDARY)
    ax.yaxis.label.set_color(TEXT_SECONDARY)
    ax.title.set_color(TEXT_PRIMARY)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(True, alpha=0.15, color=GRID_COLOR, linewidth=0.5)

    # Subtle rounded border effect
    ax.patch.set_linewidth(1)
    ax.patch.set_edgecolor("#1a2744")


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

    if download_data:
        dates_down, values_down = zip(*download_data)
        ax.fill_between(dates_down, values_down, alpha=0.2, color=CYAN)
        ax.plot(dates_down, values_down, color=CYAN, linewidth=2.5,
                label="↓ Download", marker='o', markersize=3, zorder=5)

    if upload_data:
        dates_up, values_up = zip(*upload_data)
        ax.fill_between(dates_up, values_up, alpha=0.15, color=VIOLET)
        ax.plot(dates_up, values_up, color=VIOLET_SOFT, linewidth=2,
                label="↑ Upload", marker='o', markersize=3, zorder=5)

    ax.set_title(f"Dem1chVPN — {user_name}", fontsize=14,
                 fontweight="bold", pad=15, loc="left",
                 fontfamily="sans-serif", color=TEXT_PRIMARY)
    ax.yaxis.set_major_formatter(FuncFormatter(_format_bytes_axis))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.legend(loc="upper left", framealpha=0.3, facecolor=BG_CARD,
              edgecolor=GRID_COLOR, fontsize=10, labelcolor=TEXT_PRIMARY)

    fig.autofmt_xdate()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
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
    fig, ax = plt.subplots(figsize=(10, max(4, len(users) * 0.7 + 1.5)))
    _apply_style(fig, ax)

    if not users:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                fontsize=16, color=TEXT_TERTIARY, transform=ax.transAxes)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150,
                    facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    # Sort by total traffic (largest at top)
    users = sorted(users, key=lambda u: u["upload"] + u["download"])

    names = [u["name"] for u in users]
    uploads = [u["upload"] for u in users]
    downloads = [u["download"] for u in users]

    y_pos = np.arange(len(names))
    bar_height = 0.35

    # Download bars (cyan)
    bars_down = ax.barh(y_pos - bar_height / 2, downloads,
                        height=bar_height, color=CYAN, alpha=0.85,
                        label="↓ Download", zorder=3)

    # Upload bars (violet)
    bars_up = ax.barh(y_pos + bar_height / 2, uploads,
                      height=bar_height, color=VIOLET, alpha=0.85,
                      label="↑ Upload", zorder=3)

    # Add value labels to the right of bars
    max_val = max(max(downloads) if downloads else 0,
                  max(uploads) if uploads else 0)
    for bar in bars_down:
        width = bar.get_width()
        if width > 0:
            ax.text(width + max_val * 0.02, bar.get_y() + bar.get_height() / 2,
                    _format_bytes_short(width), va="center", ha="left",
                    fontsize=8, color=CYAN_SOFT, fontfamily="monospace")

    for bar in bars_up:
        width = bar.get_width()
        if width > 0:
            ax.text(width + max_val * 0.02, bar.get_y() + bar.get_height() / 2,
                    _format_bytes_short(width), va="center", ha="left",
                    fontsize=8, color=VIOLET_SOFT, fontfamily="monospace")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=11, color=TEXT_PRIMARY, fontweight="500")
    ax.xaxis.set_major_formatter(FuncFormatter(_format_bytes_axis))

    # Title with date
    now = datetime.now()
    ax.set_title(f"Dem1chVPN • Трафик ({now.strftime('%d.%m.%Y')})",
                 fontsize=14, fontweight="bold", pad=15, loc="left",
                 fontfamily="sans-serif", color=TEXT_PRIMARY)

    ax.legend(loc="lower right", framealpha=0.3, facecolor=BG_CARD,
              edgecolor=GRID_COLOR, fontsize=10, labelcolor=TEXT_PRIMARY)

    # Add some padding on the right for labels
    if max_val > 0:
        ax.set_xlim(right=max_val * 1.2)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
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
        ax.plot(timestamps, cpu_values, color=CORAL, linewidth=2,
                label="CPU %", alpha=0.9, zorder=5)
        ax.fill_between(timestamps, cpu_values, alpha=0.1, color=CORAL)
    if timestamps and ram_values:
        ax.plot(timestamps, ram_values, color=EMERALD, linewidth=2,
                label="RAM %", alpha=0.9, zorder=5)
        ax.fill_between(timestamps, ram_values, alpha=0.1, color=EMERALD)

    ax.set_ylim(0, 100)
    ax.set_title("Dem1chVPN — Нагрузка сервера", fontsize=14,
                 fontweight="bold", pad=15, loc="left",
                 fontfamily="sans-serif", color=TEXT_PRIMARY)
    ax.set_ylabel("Загрузка %", fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.legend(loc="upper left", framealpha=0.3, facecolor=BG_CARD,
              edgecolor=GRID_COLOR, fontsize=10, labelcolor=TEXT_PRIMARY)

    fig.autofmt_xdate()
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
