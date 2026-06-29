"""
Dem1chVPN — Validators
Input validation utilities.
"""
import re


def validate_domain(domain: str) -> bool:

    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def validate_ip(ip: str) -> bool:

    octet = r'(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])'
    pattern = rf'^({octet}\.){{3}}{octet}$'
    return bool(re.match(pattern, ip))


def validate_uuid(uuid: str) -> bool:

    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid, re.IGNORECASE))


def sanitize_domain(raw: str) -> str:

    domain = raw.strip().lower()
    domain = domain.replace("https://", "").replace("http://", "")
    domain = domain.split("/")[0]
    domain = domain.split(":")[0]
    domain = domain.strip(".")
    return domain
