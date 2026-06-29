"""
Dem1chVPN — Updater Service
"""
import asyncio
import logging
import os
from pathlib import Path

from ..config import config

logger = logging.getLogger("dem1chvpn.updater")


async def _communicate(proc, timeout: int):
    # при таймауте дочерний процесс надо убить, иначе wget/curl висит зомби
    try:
        return await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise


class XrayUpdater:
    """Manages Xray-core and geo-data updates."""

    GEO_URLS = {
        "geoip": [
            "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat",
            "https://github.com/v2fly/geoip/releases/latest/download/geoip.dat",
        ],
        "geosite": [
            "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat",
            "https://github.com/v2fly/domain-list-community/releases/latest/download/dlc.dat",
        ],
    }

    async def update_xray_core(self) -> dict:
        """
        Update Xray-core to the latest version using the official installer.
        Returns: {"success": bool, "version": str, "output": str}
        """
        try:
            install_cmd = "bash -c \"$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)\" @ install"
            proc = await asyncio.create_subprocess_exec(
                "sudo", "sh", "-c", install_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await _communicate(proc, 120)
            output = stdout.decode() + stderr.decode()

            version = await self._get_version()
            success = proc.returncode == 0

            if success:
                logger.info(f"Xray-core updated to v{version}")
            else:
                logger.error(f"Xray update failed: {output[:500]}")

            return {"success": success, "version": version, "output": output[:1000]}

        except asyncio.TimeoutError:
            logger.error("Xray update timed out")
            return {"success": False, "version": "unknown", "output": "Timeout"}
        except Exception as e:
            logger.error(f"Xray update error: {e}")
            return {"success": False, "version": "unknown", "output": str(e)}

    async def update_geo_databases(self) -> dict:
        """
        Download latest geoip.dat and geosite.dat.
        Returns: {"geoip": bool, "geosite": bool}
        """
        results = {}

        for geo_type, urls in self.GEO_URLS.items():
            dest = config.GEOIP_PATH if geo_type == "geoip" else config.GEOSITE_PATH
            results[geo_type] = await self._download_with_fallback(urls, dest)

        if any(results.values()):
            await self._restart_xray()
            logger.info("Geo databases updated, Xray restarted")

        return results

    async def _download_with_fallback(self, urls: list[str], dest: str) -> bool:
        """Try downloading from each URL until one succeeds."""
        tmp = f"{dest}.tmp"
        for url in urls:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "wget", "-qO", tmp, url,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await _communicate(proc, 60)
                # подменяем рабочий файл только после полной успешной загрузки — иначе битый geo уронит Xray
                if proc.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
                    os.replace(tmp, dest)
                    logger.info(f"Downloaded {dest} from {url}")
                    return True
            except Exception as e:
                logger.warning(f"Download failed from {url}: {e}")
            finally:
                if os.path.exists(tmp):
                    try:
                        os.unlink(tmp)
                    except OSError:
                        pass

        logger.error(f"All download URLs failed for {dest}")
        return False

    async def _get_version(self) -> str:
        """Get current Xray-core version."""
        try:
            proc = await asyncio.create_subprocess_exec(
                config.XRAY_BINARY, "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await _communicate(proc, 5)
            first_line = stdout.decode().strip().split("\n")[0]
            return first_line.split(" ")[1] if " " in first_line else "unknown"
        except Exception:
            return "unknown"

    async def _restart_xray(self):
        """Restart the Xray service."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "sudo", "systemctl", "restart", "xray",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await _communicate(proc, 10)
        except Exception as e:
            logger.error(f"Xray restart failed: {e}")
