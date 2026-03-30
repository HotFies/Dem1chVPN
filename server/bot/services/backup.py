"""
XShield — Backup Service
Backup and restore operations for XShield configuration.
"""
import os
import io
import tarfile
import shutil
import logging
from pathlib import Path
from datetime import datetime

from ..config import config

logger = logging.getLogger("xshield.backup")


class BackupManager:
    """Manages backup and restore of XShield data."""

    def __init__(self):
        self.backup_dir = Path(config.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> tuple[bytes, str]:
        """
        Create a backup archive containing:
        - Xray config.json
        - SQLite database
        - .env file

        Returns: (tar_gz_bytes, filename)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"xshield_{timestamp}.tar.gz"

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            # Xray config
            if os.path.exists(config.XRAY_CONFIG_PATH):
                tar.add(config.XRAY_CONFIG_PATH, arcname="xray_config.json")

            # Database
            if os.path.exists(config.DB_PATH):
                tar.add(config.DB_PATH, arcname="xshield.db")

            # .env
            env_path = str(Path(config.DB_PATH).resolve().parent.parent / ".env")
            if os.path.exists(env_path):
                tar.add(env_path, arcname=".env")

        buf.seek(0)
        backup_bytes = buf.getvalue()

        # Also save to disk
        disk_path = self.backup_dir / filename
        with open(disk_path, "wb") as f:
            f.write(backup_bytes)

        # Clean old backups (keep last 7)
        self._cleanup_old_backups(keep=7)

        logger.info(f"Backup created: {filename} ({len(backup_bytes)} bytes)")
        return backup_bytes, filename

    def restore_from_bytes(self, data: bytes) -> dict:
        """
        Restore from a tar.gz backup file.

        Returns: {"restored": [list of restored files], "errors": [list of errors]}
        """
        result = {"restored": [], "errors": []}

        try:
            buf = io.BytesIO(data)
            with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                members = tar.getnames()

                # Security: reject archives with path traversal
                for name in members:
                    if name.startswith('/') or '..' in name:
                        result["errors"].append(f"Rejected unsafe path: {name}")
                        logger.warning(f"Path traversal attempt in backup: {name}")
                        return result

                allowed_names = {"xray_config.json", "xshield.db", ".env"}
                for name in members:
                    if name not in allowed_names:
                        continue
                    try:
                        member = tar.getmember(name)
                        f = tar.extractfile(member)
                        if f is None:
                            continue
                        content = f.read()

                        if name == "xray_config.json":
                            dest = config.XRAY_CONFIG_PATH
                        elif name == "xshield.db":
                            dest = config.DB_PATH
                        elif name == ".env":
                            dest = str(Path(config.DB_PATH).resolve().parent.parent / ".env")
                        else:
                            continue

                        # Backup current file before overwriting
                        if os.path.exists(dest):
                            shutil.copy2(dest, f"{dest}.bak")

                        with open(dest, "wb") as out:
                            out.write(content)

                        result["restored"].append(name)
                        logger.info(f"Restored: {name} -> {dest}")

                    except Exception as e:
                        result["errors"].append(f"{name}: {e}")
                        logger.error(f"Error restoring {name}: {e}")

        except Exception as e:
            result["errors"].append(f"Archive error: {e}")
            logger.error(f"Restore failed: {e}")

        return result

    def list_backups(self) -> list[dict]:
        """List available backup files."""
        backups = []
        if not self.backup_dir.exists():
            return backups

        for f in sorted(self.backup_dir.glob("xshield_*.tar.gz"), reverse=True):
            stat = f.stat()
            backups.append({
                "filename": f.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

        return backups

    def _cleanup_old_backups(self, keep: int = 7):
        """Remove old backup files, keeping only the most recent ones."""
        files = sorted(
            self.backup_dir.glob("xshield_*.tar.gz"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        for f in files[keep:]:
            try:
                f.unlink()
                logger.info(f"Removed old backup: {f.name}")
            except Exception as e:
                logger.warning(f"Could not remove {f.name}: {e}")
