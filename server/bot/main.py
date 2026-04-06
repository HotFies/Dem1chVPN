"""
Dem1chVPN Bot — Entry Point
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
from .handlers import invite, wizard, security, tickets
from .services.user_manager import UserManager
from .services.xray_config import XrayConfigManager

log_handlers = [logging.StreamHandler(sys.stdout)]
try:
    from logging.handlers import RotatingFileHandler
    log_handlers.append(RotatingFileHandler(
        "/var/log/dem1chvpn/bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    ))
except (OSError, FileNotFoundError):
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=log_handlers,
)
logger = logging.getLogger("dem1chvpn")


async def on_startup(bot: Bot):
    logger.info("🛡️ Dem1chVPN Bot starting...")

    await init_db()
    logger.info("✅ Database initialized")

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "🛡️ <b>Dem1chVPN Bot запущен!</b>\n\n"
                "Используйте /start для начала работы.",
            )
        except Exception as e:
            logger.warning(f"Could not notify admin {admin_id}: {e}")

    logger.info("✅ Dem1chVPN Bot started successfully")


async def traffic_sync_task(bot: Bot):
    from .services.xray_api import XrayAPI

    api = XrayAPI()
    mgr = UserManager()
    xray_mgr = XrayConfigManager()
    snapshot_counter = 0

    while True:
        try:
            await asyncio.sleep(60)
            snapshot_counter += 1

            all_stats = await api.get_all_user_stats(reset=True)
            if not all_stats:
                continue

            all_users = await mgr.get_all_users()
            for user in all_users:
                stats = all_stats.get(user.email)
                if stats and (stats["uplink"] > 0 or stats["downlink"] > 0):
                    await mgr.add_traffic(
                        user.id,
                        upload=stats["uplink"],
                        download=stats["downlink"],
                    )

                    await mgr.update_last_seen(user.email)

                    if snapshot_counter % 15 == 0:
                        updated_user = await mgr.get_user(user.id)
                        if updated_user:
                            await mgr.save_traffic_snapshot(
                                user.id,
                                updated_user.traffic_used_up,
                                updated_user.traffic_used_down,
                            )

                    updated_user = await mgr.get_user(user.id)
                    if not updated_user:
                        continue

                    if (
                        updated_user.is_active
                        and updated_user.traffic_limit
                        and not updated_user.warning_sent
                        and updated_user.traffic_total >= updated_user.traffic_limit * 0.8
                    ):
                        await mgr.set_warning_sent(updated_user.id, True)
                        used_pct = int(updated_user.traffic_total / updated_user.traffic_limit * 100)
                        logger.info(f"Sending 80% warning to {updated_user.name} ({used_pct}%)")

                        if updated_user.telegram_id:
                            try:
                                from .utils.formatters import format_traffic
                                await bot.send_message(
                                    updated_user.telegram_id,
                                    f"⚠️ <b>Предупреждение о трафике</b>\n\n"
                                    f"Вы использовали <b>{used_pct}%</b> трафика "
                                    f"({format_traffic(updated_user.traffic_total)} из "
                                    f"{format_traffic(updated_user.traffic_limit)}).\n\n"
                                    f"При достижении лимита аккаунт будет приостановлен.",
                                )
                            except Exception:
                                pass

                        for admin_id in config.ADMIN_IDS:
                            try:
                                await bot.send_message(
                                    admin_id,
                                    f"⚠️ <b>{updated_user.name}</b> использовал {used_pct}% трафика.",
                                )
                            except Exception:
                                pass

                    if (
                        updated_user.is_active
                        and updated_user.traffic_limit
                        and updated_user.traffic_total >= updated_user.traffic_limit
                    ):
                        logger.info(
                            f"Auto-blocking {updated_user.name}: traffic exceeded "
                            f"({updated_user.traffic_total}/{updated_user.traffic_limit})"
                        )
                        await mgr.set_user_active(updated_user.id, False)
                        await xray_mgr.remove_client(updated_user.email)
                        await mgr.log_action(
                            "auto_block_traffic",
                            target_user_id=updated_user.id,
                            details=f"Traffic {updated_user.traffic_total} >= limit {updated_user.traffic_limit}",
                        )

                        for admin_id in config.ADMIN_IDS:
                            try:
                                await bot.send_message(
                                    admin_id,
                                    f"📊 <b>Автоблокировка!</b>\n\n"
                                    f"Пользователь <b>{updated_user.name}</b> "
                                    f"заблокирован — превышен лимит трафика.",
                                )
                            except Exception:
                                pass

                        if updated_user.telegram_id:
                            try:
                                await bot.send_message(
                                    updated_user.telegram_id,
                                    "📊 <b>Лимит трафика исчерпан</b>\n\n"
                                    "Ваш VPN-аккаунт временно приостановлен.\n"
                                    "Обратитесь к администратору для продления.",
                                )
                            except Exception:
                                pass

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Traffic sync error: {e}")
            await asyncio.sleep(30)


async def expiry_check_task(bot: Bot):
    mgr = UserManager()
    xray_mgr = XrayConfigManager()

    while True:
        try:
            await asyncio.sleep(300)  # Check every 5 minutes

            expired_users = await mgr.get_expired_active_users()
            for user in expired_users:
                logger.info(f"Auto-blocking expired user: {user.name}")
                await mgr.set_user_active(user.id, False)
                await xray_mgr.remove_client(user.email)
                await mgr.log_action(
                    "auto_block_expired",
                    target_user_id=user.id,
                    details=f"Expired at {user.expiry_date}",
                )

                # Notify admin
                for admin_id in config.ADMIN_IDS:
                    try:
                        await bot.send_message(
                            admin_id,
                            f"⏰ <b>Срок действия истёк</b>\n\n"
                            f"Пользователь <b>{user.name}</b> автоматически заблокирован.",
                        )
                    except Exception:
                        pass

                if user.telegram_id:
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            "⏰ <b>Срок действия аккаунта истёк</b>\n\n"
                            "Ваш VPN-аккаунт приостановлен.\n"
                            "Обратитесь к администратору для продления.",
                        )
                    except Exception:
                        pass

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Expiry check error: {e}")
            await asyncio.sleep(60)


async def on_shutdown(bot: Bot):
    logger.info("🛡️ Dem1chVPN Bot shutting down...")
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "⚠️ Dem1chVPN Bot остановлен.")
        except Exception:
            pass


async def monthly_reset_task(bot: Bot):
    from datetime import datetime, timezone

    mgr = UserManager()
    xray_mgr = XrayConfigManager()
    last_reset_month = None

    while True:
        try:
            await asyncio.sleep(300)  # Check every 5 minutes

            now = datetime.now(timezone.utc)
            reset_day = config.TRAFFIC_RESET_DAY

            if now.day == reset_day and last_reset_month != now.month:
                logger.info(f"Monthly traffic reset triggered (day={reset_day})")

                reset_count, reactivated = await mgr.reset_and_reactivate_traffic()

                for user in reactivated:
                    await xray_mgr.add_client(user.uuid, user.email)

                last_reset_month = now.month

                # Notify admin
                for admin_id in config.ADMIN_IDS:
                    try:
                        await bot.send_message(
                            admin_id,
                            f"📊 <b>Ежемесячный сброс трафика</b>\n\n"
                            f"Сброшено: {reset_count} пользователей\n"
                            f"Разблокировано: {len(reactivated)}",
                        )
                    except Exception:
                        pass

                for user in reactivated:
                    if user.telegram_id:
                        try:
                            await bot.send_message(
                                user.telegram_id,
                                "📊 <b>Начался новый месяц!</b>\n\n"
                                "Ваш счётчик трафика сброшен.\n"
                                "Аккаунт снова активен. Используйте VPN!",
                            )
                        except Exception:
                            pass

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Monthly reset error: {e}")
            await asyncio.sleep(60)


async def auto_update_check_task(bot: Bot):
    import aiohttp

    if not config.XRAY_AUTO_UPDATE:
        return

    xray_mgr = XrayConfigManager()
    last_notified_version = None

    while True:
        try:
            await asyncio.sleep(86400)

            current_version = await xray_mgr.get_xray_version()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.github.com/repos/XTLS/Xray-core/releases/latest",
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()

            latest_version = data.get("tag_name", "").lstrip("v")

            if (
                latest_version
                and latest_version != current_version
                and latest_version != last_notified_version
            ):
                last_notified_version = latest_version
                logger.info(f"New Xray version available: v{latest_version} (current: v{current_version})")

                for admin_id in config.ADMIN_IDS:
                    try:
                        await bot.send_message(
                            admin_id,
                            f"🔄 <b>Доступно обновление Xray-core</b>\n\n"
                            f"Текущая: v{current_version}\n"
                            f"Новая: v{latest_version}\n\n"
                            f"Обновите через: ⚙️ Настройки → 🔄 Xray-core",
                        )
                    except Exception:
                        pass

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Auto-update check error: {e}")
            await asyncio.sleep(3600)


async def main():
    errors = config.validate()
    if errors:
        for err in errors:
            logger.error(f"❌ Config error: {err}")
        sys.exit(1)

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.include_router(security.router)
    dp.include_router(invite.router)
    dp.include_router(start.router)
    dp.include_router(users.router)
    dp.include_router(routing.router)
    dp.include_router(monitoring.router)
    dp.include_router(settings.router)
    dp.include_router(help_handler.router)
    dp.include_router(wizard.router)
    dp.include_router(tickets.router)

    sync_task = asyncio.create_task(traffic_sync_task(bot))
    expiry_task = asyncio.create_task(expiry_check_task(bot))
    reset_task = asyncio.create_task(monthly_reset_task(bot))
    update_task = asyncio.create_task(auto_update_check_task(bot))

    logger.info("🚀 Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        sync_task.cancel()
        expiry_task.cancel()
        reset_task.cancel()
        update_task.cancel()
        for task in [sync_task, expiry_task, reset_task, update_task]:
            try:
                await task
            except asyncio.CancelledError:
                pass


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
