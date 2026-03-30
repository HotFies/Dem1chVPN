"""
XShield — MTProto Manager Service
Manage MTProto proxy for Telegram.
"""
import asyncio
import os
from ..config import config


class MTProtoManager:
    """Manages MTProto proxy (mtg in Docker)."""

    def __init__(self):
        self.compose_dir = "/opt/xshield/server/mtproto"

    async def is_running(self) -> bool:
        """Check if mtg container is running."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "inspect", "-f", "{{.State.Running}}", "xshield-mtproto",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            return stdout.decode().strip() == "true"
        except Exception:
            return False

    def is_installed(self) -> bool:
        """Check if MTProto config exists."""
        return os.path.exists(f"{self.compose_dir}/config.toml")

    async def start(self) -> bool:
        """Start MTProto proxy."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "compose", "up", "-d",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.compose_dir,
            )
            await asyncio.wait_for(proc.communicate(), timeout=30)
            return True
        except Exception:
            return False

    async def stop(self) -> bool:
        """Stop MTProto proxy."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "compose", "down",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.compose_dir,
            )
            await asyncio.wait_for(proc.communicate(), timeout=30)
            return True
        except Exception:
            return False

    async def restart(self) -> bool:
        """Restart MTProto proxy."""
        await self.stop()
        return await self.start()

    def get_secret(self) -> str:
        """Get MTProto secret from .env."""
        return os.getenv("MTPROTO_SECRET", "")

    def get_proxy_link(self) -> str:
        """Generate Telegram MTProto proxy link."""
        secret = self.get_secret()
        server_ip = config.SERVER_IP
        port = config.SERVER_PORT  # 443, via Xray fallback

        if not secret:
            return ""

        return f"tg://proxy?server={server_ip}&port={port}&secret={secret}"

    def get_https_link(self) -> str:
        """Generate HTTPS proxy link."""
        secret = self.get_secret()
        server_ip = config.SERVER_IP
        port = config.SERVER_PORT

        if not secret:
            return ""

        return f"https://t.me/proxy?server={server_ip}&port={port}&secret={secret}"

    async def get_formatted_status(self) -> str:
        """Get formatted status for bot."""
        running = await self.is_running()
        installed = self.is_installed()

        if not installed:
            return "💬 MTProto Proxy: ❌ Не установлен\n   Запустите: /opt/xshield/server/mtproto/setup.sh"

        status = "🟢 Работает" if running else "🔴 Остановлен"
        link = self.get_proxy_link()

        text = f"💬 <b>MTProto Proxy</b>\n\n  Статус: {status}\n"
        if link:
            text += f"\n  🔗 Ссылка для Telegram:\n  <code>{link}</code>\n"
            text += "\n  <i>Добавьте в: Настройки Telegram → Данные → Прокси</i>"

        return text
