"""
XShield Bot — Entry Point
Main bot application with aiogram 3.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from .config import config
from .database import init_db
from .handlers import start, users, routing, monitoring, settings, help as help_handler
from .handlers import invite, wizard, security

# Configure logging with rotation
log_handlers = [logging.StreamHandler(sys.stdout)]
try:
    from logging.handlers import RotatingFileHandler
    log_handlers.append(RotatingFileHandler(
        "/var/log/xshield/bot.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB per file
        backupCount=3,
        encoding="utf-8",
    ))
except (OSError, FileNotFoundError):
    pass  # OK on Windows / development

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=log_handlers,
)
logger = logging.getLogger("xshield")


async def on_startup(bot: Bot):
    """Called when bot starts."""
    logger.info("🛡️ XShield Bot starting...")

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Notify admin
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "🛡️ <b>XShield Bot запущен!</b>\n\n"
                "Используйте /start для начала работы.",
            )
        except Exception as e:
            logger.warning(f"Could not notify admin {admin_id}: {e}")

    logger.info("✅ XShield Bot started successfully")


async def traffic_sync_task(bot: Bot):
    """
    Background task: periodically sync traffic stats from Xray gRPC API.
    Runs every 60 seconds, queries Xray Stats, updates DB.
    """
    from .services.xray_api import XrayAPI
    from .services.user_manager import UserManager

    api = XrayAPI()
    mgr = UserManager()

    while True:
        try:
            await asyncio.sleep(60)  # Check every 60 seconds

            # Get stats and reset counters
            all_stats = await api.get_all_user_stats(reset=True)
            if not all_stats:
                continue

            # Update each user's traffic
            users = await mgr.get_all_users()
            for user in users:
                stats = all_stats.get(user.email)
                if stats and (stats["uplink"] > 0 or stats["downlink"] > 0):
                    await mgr.add_traffic(
                        user.id,
                        upload=stats["uplink"],
                        download=stats["downlink"],
                    )

                    # Re-read user to get fresh traffic_total after update
                    updated_user = await mgr.get_user(user.id)
                    if not updated_user:
                        continue

                    # Check traffic limit
                    if updated_user.traffic_limit and updated_user.traffic_total > updated_user.traffic_limit:
                        logger.info(f"User {updated_user.name} exceeded traffic limit")
                        # Notify admin
                        for admin_id in config.ADMIN_IDS:
                            try:
                                await bot.send_message(
                                    admin_id,
                                    f"📊 <b>Лимит трафика!</b>\n\n"
                                    f"Пользователь <b>{updated_user.name}</b> превысил лимит.",
                                )
                            except Exception:
                                pass

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Traffic sync error: {e}")
            await asyncio.sleep(30)


async def on_shutdown(bot: Bot):
    """Called when bot stops."""
    logger.info("🛡️ XShield Bot shutting down...")
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "⚠️ XShield Bot остановлен.")
        except Exception:
            pass


async def main():
    """Main entry point."""
    # Validate config
    errors = config.validate()
    if errors:
        for err in errors:
            logger.error(f"❌ Config error: {err}")
        sys.exit(1)

    # Create bot & dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register event handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Register routers (handlers)
    dp.include_router(security.router)  # Must be first (middleware)
    dp.include_router(start.router)
    dp.include_router(users.router)
    dp.include_router(routing.router)
    dp.include_router(monitoring.router)
    dp.include_router(settings.router)
    dp.include_router(help_handler.router)
    dp.include_router(invite.router)
    dp.include_router(wizard.router)

    # Start background tasks
    sync_task = asyncio.create_task(traffic_sync_task(bot))

    # Start polling
    logger.info("🚀 Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass


def run():
    """Entry point for systemd service."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
