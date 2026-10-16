import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple


BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback IPv4
    ipaddress.ip_network("10.0.0.0/8"),       # RFC1918 Private
    ipaddress.ip_network("172.16.0.0/12"),    # RFC1918 Private
    ipaddress.ip_network("192.168.0.0/16"),   # RFC1918 Private
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / Cloud metadata (AWS, GCP, Azure)
    ipaddress.ip_network("0.0.0.0/8"),        # Current network
    ipaddress.ip_network("::1/128"),          # Loopback IPv6
    ipaddress.ip_network("fc00::/7"),         # Unique local address IPv6
    ipaddress.ip_network("fe80::/10"),        # Link-local IPv6
]


def is_safe_url(url: str, allowed_ports: Tuple[int, ...] = (80, 443)) -> Tuple[bool, str]:
    """
    Validates that a URL is safe to crawl and cannot be used for SSRF attacks.
    Returns (is_safe, error_reason).
    """
    if not url or not isinstance(url, str):
        return False, "Empty or invalid URL"

    try:
        parsed = urlparse(url.strip())
    except Exception as e:
        return False, f"Malformed URL: {e}"

    # Only HTTP and HTTPS
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported scheme: '{parsed.scheme}'. Only http and https are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL has no valid hostname."

    # Reject localhost directly
    if hostname.lower() in ("localhost", "localhost.localdomain", "127.0.0.1", "::1"):
        return False, "Localhost access is strictly prohibited."

    # Validate port
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    if port not in allowed_ports:
        return False, f"Port {port} is not in allowed outbound ports {allowed_ports}."

    # Resolve IP and verify not in private / cloud metadata ranges
    try:
        resolved_ips = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in resolved_ips:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            for blocked_net in BLOCKED_NETWORKS:
                if ip_obj in blocked_net:
                    return False, f"Target IP {ip_str} belongs to protected/private subnet {blocked_net}."

            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                return False, f"Target IP {ip_str} is reserved or non-public."

    except socket.gaierror as e:
        return False, f"DNS resolution failed for {hostname}: {e}"
    except Exception as e:
        return False, f"IP safety verification failed: {e}"

    return True, ""

