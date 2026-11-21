import ipaddress
import socket
import html
from urllib.parse import urlparse, urljoin
from typing import Tuple, List, Dict, Any, Optional
import httpx


# RFC 6052 Well-Known NAT64 / DNS64 Prefix
NAT64_WELL_KNOWN_PREFIX = ipaddress.IPv6Network("64:ff9b::/96")
# RFC 8215 Local-Use NAT64 Prefix
NAT64_LOCAL_PREFIX = ipaddress.IPv6Network("64:ff9b:1::/48")
# IPv4-mapped IPv6
IPV4_MAPPED_IPV6_PREFIX = ipaddress.IPv6Network("::ffff:0:0/96")


def is_ip_restricted(ip_str: str) -> Tuple[bool, str]:
    """
    Check if an IP address string represents a private, loopback, link-local,
    multicast, or internal network address.
    
    Correctly recognizes RFC 6052 / RFC 8215 NAT64/DNS64 translated addresses,
    inspecting the embedded IPv4 address rather than falsely rejecting them as 'reserved'.
    """
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return True, f"Invalid IP address format: {ip_str}"

    # Handle IPv6
    if isinstance(ip_obj, ipaddress.IPv6Address):
        # Check if this is an IPv4-mapped or NAT64-translated address
        if ip_obj in IPV4_MAPPED_IPV6_PREFIX or ip_obj in NAT64_WELL_KNOWN_PREFIX or ip_obj in NAT64_LOCAL_PREFIX:
            # Extract the embedded IPv4 address (last 32 bits)
            embedded_ipv4 = ipaddress.IPv4Address(ip_obj.packed[-4:])
            if (
                embedded_ipv4.is_private or
                embedded_ipv4.is_loopback or
                embedded_ipv4.is_link_local or
                embedded_ipv4.is_multicast or
                embedded_ipv4.is_reserved or
                embedded_ipv4.is_unspecified
            ):
                return True, f"Embedded IPv4 {embedded_ipv4} inside NAT64/DNS64 is private/restricted"
            # Embedded IPv4 is public! Safe to use.
            return False, ""

        # For normal IPv6:
        if (
            ip_obj.is_private or
            ip_obj.is_loopback or
            ip_obj.is_link_local or
            ip_obj.is_multicast or
            ip_obj.is_reserved or
            ip_obj.is_unspecified
        ):
            return True, f"IPv6 {ip_str} is private or restricted"

    # Handle IPv4
    elif isinstance(ip_obj, ipaddress.IPv4Address):
        if (
            ip_obj.is_private or
            ip_obj.is_loopback or
            ip_obj.is_link_local or
            ip_obj.is_multicast or
            ip_obj.is_reserved or
            ip_obj.is_unspecified
        ):
            return True, f"IPv4 {ip_str} is private or restricted"

    return False, ""


def is_safe_url(url: str) -> Tuple[bool, str]:
    """
    Validate that a URL is safe to fetch and does not attempt SSRF against
    private, loopback, or internal network addresses.
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or invalid."
    
    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Malformed URL structure."

    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported scheme '{parsed.scheme}'. Only http and https are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL missing valid hostname."

    # Prevent direct localhost aliases & metadata endpoints
    lower_host = hostname.lower()
    if lower_host in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "169.254.169.254", "metadata.google.internal"):
        return False, "Access to localhost or internal network is prohibited."

    # Prevent common cloud internal suffixes
    if lower_host.endswith(".internal") or lower_host.endswith(".local") or lower_host.endswith(".localhost"):
        return False, "Access to internal domain zone is prohibited."

    try:
        # Resolve hostname to check all returned IPs
        addr_info = socket.getaddrinfo(hostname, None)
        if not addr_info:
            return False, f"No DNS records resolved for '{hostname}'."
        
        # Check every IP
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            restricted, reason = is_ip_restricted(ip_str)
            if restricted:
                return False, f"Access to restricted or private network IP ({ip_str}) is prohibited: {reason}"
    except socket.gaierror:
        return False, f"Could not resolve domain '{hostname}'."
    except Exception as e:
        return False, f"Security validation error: {str(e)}"

    return True, ""


def resolve_safe_redirects(
    initial_url: str,
    max_redirects: int = 6,
    timeout: float = 10.0
) -> Tuple[bool, str, str, List[Dict[str, Any]]]:
    """
    Follow redirect chains securely (e.g. for short URLs like dl.flipkart.com/s/..., amzn.to/...).
    Every hop in the redirect chain is validated with is_safe_url to prevent SSRF redirect attacks.
    
    Returns:
        (success: bool, final_url: str, error_message: str, redirect_chain: list)
    """
    chain: List[Dict[str, Any]] = []
    current_url = initial_url.strip()

    # Step 1: Validate initial URL
    safe, err = is_safe_url(current_url)
    if not safe:
        return False, current_url, err, chain

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        with httpx.Client(follow_redirects=False, timeout=timeout, headers=headers) as client:
            for step in range(max_redirects):
                try:
                    resp = client.get(current_url)
                except httpx.TimeoutException:
                    return False, current_url, f"Connection timed out at step {step + 1} ({current_url})", chain
                except Exception as exc:
                    return False, current_url, f"HTTP error resolving redirect: {exc}", chain

                status = resp.status_code
                location = resp.headers.get("location")

                chain.append({
                    "step": step + 1,
                    "url": current_url,
                    "status_code": status,
                    "location": location
                })

                if status in (301, 302, 303, 307, 308) and location:
                    next_url = urljoin(current_url, location)
                    
                    # Validate next URL against SSRF
                    is_safe_next, next_err = is_safe_url(next_url)
                    if not is_safe_next:
                        return False, next_url, f"Redirect to unsafe destination blocked ({next_url}): {next_err}", chain
                    
                    current_url = next_url
                else:
                    # Non-redirect status reached (e.g., 200, 404, etc.)
                    break

        return True, current_url, "", chain

    except Exception as e:
        return False, current_url, f"Unexpected error during redirect resolution: {str(e)}", chain


def sanitize_text(text: str) -> str:
    """HTML sanitize text to neutralize potential script injection in comment rendering."""
    if not text:
        return ""
    return html.escape(text.strip())
