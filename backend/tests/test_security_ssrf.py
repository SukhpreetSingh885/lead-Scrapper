import pytest
from app.utils.ssrf_guard import is_safe_url


def test_ssrf_blocks_private_and_loopback_ips():
    dangerous_urls = [
        "http://localhost:8000/api/admin",
        "http://127.0.0.1/etc/passwd",
        "http://127.0.0.1:5432",
        "http://10.0.0.1/admin",
        "http://192.168.1.1/router",
        "http://172.16.0.1/internal",
        "http://169.254.169.254/latest/meta-data/",  # AWS metadata endpoint
        "http://[::1]/internal",
    ]

    for url in dangerous_urls:
        safe, reason = is_safe_url(url)
        assert safe is False, f"Expected {url} to be blocked by SSRF guard, but passed!"
        assert len(reason) > 0


def test_ssrf_blocks_unsupported_schemes():
    bad_schemes = [
        "file:///etc/passwd",
        "ftp://example.com/file",
        "gopher://example.com",
        "data:text/html,<script>alert(1)</script>",
    ]

    for url in bad_schemes:
        safe, reason = is_safe_url(url)
        assert safe is False
        assert "Unsupported scheme" in reason


def test_ssrf_permits_public_domains():
    safe, _ = is_safe_url("https://www.google.com")
    assert safe is True

    safe, _ = is_safe_url("https://httpbin.org/get")
    assert safe is True

