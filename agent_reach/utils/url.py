"""Security helpers for untrusted URLs."""

from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urlsplit

import requests
import urllib3
import urllib3.connection
import urllib3.connectionpool
import urllib3.util.connection
from requests.adapters import HTTPAdapter

_BLOCKED_PUBLIC_FETCH_HOSTS = {
    "home.arpa",
    "instance-data",
    "internal",
    "ip6-localhost",
    "ip6-loopback",
    "lan",
    "local",
    "localdomain",
    "localhost",
    "metadata.google.internal",
}
_BLOCKED_PUBLIC_FETCH_SUFFIXES = (
    ".home.arpa",
    ".internal",
    ".lan",
    ".local",
    ".localdomain",
    ".localhost",
)


def _literal_ip_address(
    host: str,
) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    """Parse canonical and legacy IPv4 literal spellings without DNS."""
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass

    try:
        packed = socket.inet_aton(host)
    except OSError:
        return None
    return ipaddress.IPv4Address(packed)


def normalize_public_http_url(url: str) -> str:
    """Normalize a URL or reject targets that are not clearly public HTTP(S)."""
    candidate = (url or "").strip()
    if (
        not candidate
        or "\\" in candidate
        or any(
            character.isspace() or ord(character) < 0x20 or ord(character) == 0x7F
            for character in candidate
        )
    ):
        raise ValueError("only public HTTP(S) URLs are allowed")
    if "://" not in candidate:
        candidate = f"https://{candidate}"

    try:
        parsed = urlsplit(candidate)
        host = (parsed.hostname or "").lower().rstrip(".")
        # Accessing the port rejects malformed or out-of-range authorities.
        _ = parsed.port
    except (TypeError, ValueError):
        raise ValueError("only public HTTP(S) URLs are allowed") from None

    literal_address = _literal_ip_address(host)
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or "%" in host
        or host in _BLOCKED_PUBLIC_FETCH_HOSTS
        or host.endswith(_BLOCKED_PUBLIC_FETCH_SUFFIXES)
        or ("." not in host and literal_address is None)
        or (literal_address is not None and not literal_address.is_global)
    ):
        raise ValueError("only public HTTP(S) URLs are allowed")

    return parsed.geturl()


def domain_matches(host: str, *domains: str) -> bool:
    """Match a hostname/cookie domain exactly or as a real subdomain."""
    normalized_host = (host or "").lower().lstrip(".").rstrip(".")
    if not normalized_host:
        return False
    for domain in domains:
        allowed = domain.lower().lstrip(".").rstrip(".")
        if normalized_host == allowed or normalized_host.endswith("." + allowed):
            return True
    return False


def host_matches(url: str, *domains: str) -> bool:
    """Return whether *url* has an exact allowed host or a real subdomain.

    Only HTTP(S) URLs without userinfo are accepted. Using ``hostname`` rather
    than substring matching prevents lookalikes such as ``x.com.evil.test`` and
    userinfo disguises such as ``x.com@evil.test``.
    """
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        # ``hostname`` is permissive: malformed or out-of-range ports only
        # raise when ``port`` is accessed. Force that validation here so
        # hostile authorities fail closed.
        _ = parsed.port
    except (TypeError, ValueError):
        return False

    if parsed.scheme.lower() not in {"http", "https"}:
        return False
    if not host or parsed.username is not None or parsed.password is not None:
        return False

    return domain_matches(host, *domains)


def _safe_create_connection(address: tuple[str, int], *args: Any, **kwargs: Any) -> socket.socket:
    """Enforce that all resolved and connected IPs are strictly public/global."""
    host, port = address
    clean_host = host.strip("[]") if host.startswith("[") else host
    family = urllib3.util.connection.allowed_gai_family()
    try:
        infos = socket.getaddrinfo(clean_host, port, family, socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Cannot resolve host {clean_host}.") from exc

    for res in infos:
        ip = res[4][0]
        if not ipaddress.ip_address(ip).is_global:
            raise ValueError(f"Connection to private/internal IP {ip} is blocked.")

    sock = urllib3.util.connection.create_connection(address, *args, **kwargs)
    peer_ip = sock.getpeername()[0]
    if not ipaddress.ip_address(peer_ip).is_global:
        sock.close()
        raise ValueError(f"Blocked connection to non-global IP: {peer_ip}")
    return sock


class SafeHTTPConnection(urllib3.connection.HTTPConnection):
    def _new_conn(self) -> socket.socket:
        try:
            return _safe_create_connection(
                (self._dns_host, self.port),
                self.timeout,
                source_address=self.source_address,
                socket_options=self.socket_options,
            )
        except OSError as e:
            raise urllib3.exceptions.NewConnectionError(self, f"Failed: {e}") from e


class SafeHTTPSConnection(urllib3.connection.HTTPSConnection):
    def _new_conn(self) -> socket.socket:
        try:
            return _safe_create_connection(
                (self._dns_host, self.port),
                self.timeout,
                source_address=self.source_address,
                socket_options=self.socket_options,
            )
        except OSError as e:
            raise urllib3.exceptions.NewConnectionError(self, f"Failed: {e}") from e


class SafeHTTPConnectionPool(urllib3.connectionpool.HTTPConnectionPool):
    ConnectionCls: Any = SafeHTTPConnection  # type: ignore[assignment]


class SafeHTTPSConnectionPool(urllib3.connectionpool.HTTPSConnectionPool):
    ConnectionCls: Any = SafeHTTPSConnection  # type: ignore[assignment]


class SafePoolManager(urllib3.PoolManager):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.pool_classes_by_scheme = {
            "http": SafeHTTPConnectionPool,
            "https": SafeHTTPSConnectionPool,
        }


class SafeHTTPAdapter(HTTPAdapter):
    """HTTPAdapter enforcing SSRF and DNS rebinding protections at socket creation."""
    def init_poolmanager(self, connections: int, maxsize: int, block: bool = False, **pool_kwargs: Any) -> None:
        self.poolmanager = SafePoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs,
        )


def create_safe_session() -> requests.Session:
    """Return a requests.Session mounted with SafeHTTPAdapter for http and https."""
    session = requests.Session()
    adapter = SafeHTTPAdapter()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
