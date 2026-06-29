from urllib.parse import quote


def win_sub(sub_url: str) -> str:
    return f"dem1chvpn://import/{quote(sub_url, safe='')}"


def win_route(routing_b64: str) -> str:
    return f"dem1chvpn://import_route/{quote(routing_b64, safe='')}"
