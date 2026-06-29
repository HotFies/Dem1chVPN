"""
Dem1chVPN Bot — Configuration
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(ENV_PATH)


def _parse_int_env(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        import logging
        logging.getLogger("dem1chvpn.config").warning(
            f"Invalid int for {key}='{raw}', using default {default}"
        )
        return default


def _parse_admin_ids() -> list[int]:
    ids = []
    for x in os.getenv("ADMIN_IDS", "").split(","):
        x = x.strip()
        if not x:
            continue
        try:
            ids.append(int(x))
        except ValueError:
            import logging
            logging.getLogger("dem1chvpn.config").warning(
                f"Skipping non-numeric ADMIN_ID: '{x}'"
            )
    return ids


@dataclass
class Config:

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: list[int] = field(default_factory=_parse_admin_ids)
    PIN_CODE: str = os.getenv("PIN_CODE", "0000")

    XRAY_API_HOST: str = os.getenv("XRAY_API_HOST", "127.0.0.1")
    XRAY_API_PORT: int = _parse_int_env("XRAY_API_PORT", 10085)
    XRAY_CONFIG_PATH: str = os.getenv("XRAY_CONFIG_PATH", "/usr/local/etc/xray/config.json")
    XRAY_BINARY: str = os.getenv("XRAY_BINARY", "/usr/local/bin/xray")
    XRAY_INBOUND_TAG: str = os.getenv("XRAY_INBOUND_TAG", "vless-reality")

    SERVER_IP: str = os.getenv("SERVER_IP", "")
    SERVER_PORT: int = _parse_int_env("SERVER_PORT", 443)

    REALITY_DEST: str = os.getenv("REALITY_DEST", "dl.google.com:443")
    REALITY_SNI: str = os.getenv("REALITY_SNI", "dl.google.com")
    REALITY_PRIVATE_KEY: str = os.getenv("REALITY_PRIVATE_KEY", "")
    REALITY_PUBLIC_KEY: str = os.getenv("REALITY_PUBLIC_KEY", "")
    REALITY_SHORT_ID: str = os.getenv("REALITY_SHORT_ID", "")

    DB_PATH: str = os.getenv("DB_PATH", str(
        Path(__file__).resolve().parent.parent / "data" / "dem1chvpn.db"
    ))

    SUB_HOST: str = os.getenv("SUB_HOST", "0.0.0.0")
    SUB_PORT: int = _parse_int_env("SUB_PORT", 8080)
    SUB_DOMAIN: str = os.getenv("SUB_DOMAIN", "")
    SUB_EXTERNAL_PORT: int = _parse_int_env("SUB_EXTERNAL_PORT", 8443)

    GEOIP_PATH: str = os.getenv("GEOIP_PATH", "/usr/local/share/xray/geoip.dat")
    GEOSITE_PATH: str = os.getenv("GEOSITE_PATH", "/usr/local/share/xray/geosite.dat")

    BACKUP_DIR: str = os.getenv("BACKUP_DIR", "/opt/dem1chvpn/backups")

    ADGUARD_ENABLED: bool = os.getenv("ADGUARD_ENABLED", "false").lower() == "true"
    WARP_ENABLED: bool = os.getenv("WARP_ENABLED", "false").lower() == "true"
    MTPROTO_ENABLED: bool = os.getenv("MTPROTO_ENABLED", "false").lower() == "true"

    HYSTERIA_ENABLED: bool = os.getenv("HYSTERIA_ENABLED", "false").lower() == "true"
    HYSTERIA_DOMAIN: str = os.getenv("HYSTERIA_DOMAIN", "")
    HYSTERIA_PORT: int = _parse_int_env("HYSTERIA_PORT", 8444)
    HYSTERIA_OBFS_PASSWORD: str = os.getenv("HYSTERIA_OBFS_PASSWORD", "")
    HYSTERIA_ACME_EMAIL: str = os.getenv("HYSTERIA_ACME_EMAIL", "")
    HYSTERIA_CONFIG_PATH: str = os.getenv("HYSTERIA_CONFIG_PATH", "/etc/hysteria/config.yaml")
    HYSTERIA_BINARY: str = os.getenv("HYSTERIA_BINARY", "/usr/local/bin/hysteria")

    TRAFFIC_RESET_DAY: int = _parse_int_env("TRAFFIC_RESET_DAY", 1)
    XRAY_AUTO_UPDATE: bool = os.getenv("XRAY_AUTO_UPDATE", "true").lower() == "true"

    DEFAULT_PROXY_DOMAINS: list[str] = field(default_factory=lambda: [
        "claude.ai", "anthropic.com",
        "chat.openai.com", "openai.com", "chatgpt.com",
        "gemini.google.com", "bard.google.com", "aistudio.google.com",
        "notebooklm.google.com", "notebooklm-pa.googleapis.com",
        "generativelanguage.googleapis.com",
        "youtube.com", "googlevideo.com", "ytimg.com", "yt.be",
        "youtu.be", "youtube-nocookie.com",
        "discord.com", "discord.gg", "discordapp.com", "discord.media",
        "web.telegram.org", "t.me", "telegram.org",
        "web.whatsapp.com", "whatsapp.com", "whatsapp.net",
        "instagram.com", "cdninstagram.com",
        "tiktok.com", "tiktokv.com", "musical.ly", "tiktokcdn.com",
        "isnssdk.com", "byteoversea.com", "ibytedtos.com",
        "byteimg.com", "muscdn.com", "pstatp.com",
    ])

    def validate(self) -> list[str]:
        errors = []
        if not self.BOT_TOKEN:
            errors.append("BOT_TOKEN is not set")
        if not self.ADMIN_IDS:
            errors.append("ADMIN_IDS is not set")
        if not self.SERVER_IP:
            errors.append("SERVER_IP is not set")
        if not self.REALITY_PRIVATE_KEY:
            errors.append("REALITY_PRIVATE_KEY is not set")
        if not self.REALITY_PUBLIC_KEY:
            errors.append("REALITY_PUBLIC_KEY is not set")
        if not self.REALITY_SHORT_ID:
            errors.append("REALITY_SHORT_ID is not set")
        return errors

    @property
    def sub_base_url(self) -> str:
        domain = self.SUB_DOMAIN or self.SERVER_IP
        return f"https://{domain}:{self.SUB_EXTERNAL_PORT}"


config = Config()
