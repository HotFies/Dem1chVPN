"""
XShield — Validators
Input validation utilities.
"""
import re


def validate_domain(domain: str) -> bool:
    """Validate a domain name."""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def validate_ip(ip: str) -> bool:
    """Validate an IPv4 address."""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    parts = ip.split('.')
    return all(0 <= int(p) <= 255 for p in parts)


def validate_uuid(uuid: str) -> bool:
    """Validate UUID format."""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid, re.IGNORECASE))


def sanitize_domain(raw: str) -> str:
    """Clean up user-entered domain."""
    domain = raw.strip().lower()
    domain = domain.replace("https://", "").replace("http://", "")
    domain = domain.split("/")[0]
    domain = domain.split(":")[0]  # Remove port
    domain = domain.strip(".")
    return domain
