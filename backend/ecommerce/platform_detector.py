import re
from typing import Tuple, Optional, Dict, Any
from urllib.parse import urlparse
from backend.utils.security import is_safe_url, resolve_safe_redirects


PLATFORM_METADATA: Dict[str, Dict[str, str]] = {
    "amazon": {
        "key": "amazon",
        "display_name": "Amazon",
        "domain": "amazon.com",
        "color": "#f59e0b",
        "icon": "🛒"
    },
    "flipkart": {
        "key": "flipkart",
        "display_name": "Flipkart",
        "domain": "flipkart.com",
        "color": "#2563eb",
        "icon": "⚡"
    },
    "meesho": {
        "key": "meesho",
        "display_name": "Meesho",
        "domain": "meesho.com",
        "color": "#db2777",
        "icon": "🛍️"
    },
    "ajio": {
        "key": "ajio",
        "display_name": "AJIO",
        "domain": "ajio.com",
        "color": "#059669",
        "icon": "🏷️"
    },
    "myntra": {
        "key": "myntra",
        "display_name": "Myntra",
        "domain": "myntra.com",
        "color": "#e11d48",
        "icon": "👗"
    }
}


class PlatformDetector:
    """
    Automatic hostname-based detection for the 5 targeted e-commerce platforms.
    Resolves short URLs safely and verifies destination domains.
    """

    @classmethod
    def detect_from_url(cls, raw_url: str) -> Tuple[Optional[str], str, Optional[Dict[str, str]], str]:
        """
        Detects platform from raw URL.
        Returns:
            (platform_key, resolved_url, metadata_dict, error_message)
        """
        if not raw_url or not isinstance(raw_url, str):
            return None, "", None, "Empty or invalid URL provided."

        url = raw_url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        try:
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()
        except Exception:
            return None, url, None, "Invalid URL structure."

        is_short_url = any(s in hostname for s in ["amzn.to", "amzn.in", "fkrt.it", "bit.ly", "tinyurl.com"]) or ("flipkart.com" in hostname and "/s/" in parsed.path)

        if is_short_url:
            safe, resolved_url, err_msg, _ = resolve_safe_redirects(url)
            if not safe:
                return None, url, None, f"Security validation rejected URL: {err_msg}"
            hostname = (urlparse(resolved_url).hostname or "").lower()
        else:
            safe, err_msg = is_safe_url(url)
            if not safe:
                return None, url, None, f"Security validation rejected URL: {err_msg}"
            resolved_url = url

        # Platform Matching
        amazon_domains = ("amazon.in", "amazon.com", "amazon.co.uk", "amazon.ca", "amazon.de",
                          "amazon.fr", "amazon.it", "amazon.es", "amazon.co.jp", "amazon.com.au",
                          "amazon.com.br", "amazon.com.mx", "amazon.nl", "amazon.sg", "amazon.ae",
                          "amazon.sa", "amazon.com.tr", "amazon.pl", "amazon.se",
                          "amazon.com.be", "amazon.com.eg", "amazon.com.ng", "amzn.to", "amzn.in")
        if any(hostname == domain or hostname.endswith("." + domain) for domain in amazon_domains):
            return "amazon", resolved_url, PLATFORM_METADATA["amazon"], ""
        elif "flipkart.com" in hostname or "fkrt.it" in hostname:
            return "flipkart", resolved_url, PLATFORM_METADATA["flipkart"], ""
        elif "meesho.com" in hostname:
            return "meesho", resolved_url, PLATFORM_METADATA["meesho"], ""
        elif "ajio.com" in hostname:
            return "ajio", resolved_url, PLATFORM_METADATA["ajio"], ""
        elif "myntra.com" in hostname:
            return "myntra", resolved_url, PLATFORM_METADATA["myntra"], ""

        return None, resolved_url, None, f"Unsupported platform for domain '{hostname}'. Supported: Amazon, Flipkart, Meesho, AJIO, Myntra."
