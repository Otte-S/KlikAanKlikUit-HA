"""Local network discovery for the ICS-2000 hub.

Sends the same UDP broadcast the library uses in get_hub_ip() and collects
every hub that replies. Only a real ICS-2000 answers on port 2012, so a reply
is a reliable signal. The reply's source address gives the hub IP; some
firmwares also include the MAC in the payload, which we parse when present.
"""
from __future__ import annotations

import logging
import socket
import time

_LOGGER = logging.getLogger(__name__)

DISCOVERY_PORT = 2012
# Same probe payload as ics2000_python.Core.get_hub_ip.
_PROBE = bytes.fromhex(
    "010003ffffffffffffca000000010400044795000401040004000400040000000000000000020000003000"
)


def _parse_mac(payload: bytes) -> str | None:
    """Best-effort MAC extraction from a hub reply.

    The reply echoes a header similar to the probe; bytes 3-8 of the probe are
    the broadcast MAC (ff:ff:ff:ff:ff:ff). In replies observed from the hub the
    same offset carries the hub's own MAC. This is best-effort: if the bytes
    look like a broadcast/zero MAC we treat it as unknown and fall back to the
    IP for identification.
    """
    if len(payload) < 9:
        return None
    mac_bytes = payload[3:9]
    if mac_bytes in (b"\xff\xff\xff\xff\xff\xff", b"\x00\x00\x00\x00\x00\x00"):
        return None
    return ":".join(f"{b:02x}" for b in mac_bytes)


def discover_hubs(timeout: int = 3) -> list[dict[str, str]]:
    """Broadcast and return a list of {"ip": ip, "mac": mac|""} for replies.

    Blocking - run in the executor. Kept short (default 3s) because discovery
    runs periodically and shouldn't hold things up or spam the network.
    """
    results: dict[str, dict[str, str]] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.5)
        try:
            sock.sendto(_PROBE, ("255.255.255.255", DISCOVERY_PORT))
        except OSError as err:
            _LOGGER.debug("Discovery broadcast failed: %s", err)
            return []

        end_at = time.monotonic() + timeout
        while time.monotonic() < end_at:
            try:
                payload, addr = sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break
            ip = addr[0]
            if ip not in results:
                results[ip] = {"ip": ip, "mac": _parse_mac(payload) or ""}
    finally:
        sock.close()

    return list(results.values())
