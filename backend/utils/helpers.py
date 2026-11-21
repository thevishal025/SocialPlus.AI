import re
from typing import Optional
from urllib.parse import urlparse, parse_qs


def extract_youtube_video_id(input_str: str) -> Optional[str]:
    """
    Extract YouTube 11-character video ID from:
    - Standard watch URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - Short URL: https://youtu.be/dQw4w9WgXcQ
    - Shorts URL: https://www.youtube.com/shorts/dQw4w9WgXcQ
    - Embed URL: https://www.youtube.com/embed/dQw4w9WgXcQ
    - Live URL: https://www.youtube.com/live/dQw4w9WgXcQ
    - Direct ID: dQw4w9WgXcQ
    """
    if not input_str:
        return None
    input_str = input_str.strip()

    # Direct 11-char ID
    if re.fullmatch(r"^[a-zA-Z0-9_-]{11}$", input_str):
        return input_str

    try:
        parsed = urlparse(input_str)
        # youtu.be/VIDEO_ID
        if "youtu.be" in parsed.netloc:
            path_parts = parsed.path.strip("/").split("/")
            if path_parts and len(path_parts[0]) == 11:
                return path_parts[0]

        # youtube.com
        if "youtube.com" in parsed.netloc:
            # /watch?v=VIDEO_ID
            qs = parse_qs(parsed.query)
            if "v" in qs and qs["v"] and len(qs["v"][0]) == 11:
                return qs["v"][0]
            
            # /shorts/VIDEO_ID, /embed/VIDEO_ID, /live/VIDEO_ID
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) >= 2 and parts[0] in ("shorts", "embed", "live", "v"):
                if len(parts[1]) == 11:
                    return parts[1]

        # Regex fallback
        match = re.search(r"(?:v=|\/)([a-zA-Z0-9_-]{11})(?:\?|&|\/|$)", input_str)
        if match:
            return match.group(1)
    except Exception:
        pass

    return None


def extract_instagram_post_id(input_str: str) -> Optional[str]:
    """
    Extract Instagram post shortcode or identifier:
    - https://www.instagram.com/p/C6XYZ123/
    - https://www.instagram.com/reel/C6XYZ123/
    """
    if not input_str:
        return None
    input_str = input_str.strip()
    match = re.search(r"instagram\.com\/(?:p|reel|tv)\/([a-zA-Z0-9_-]+)", input_str)
    if match:
        return match.group(1)
    if re.fullmatch(r"^[a-zA-Z0-9_-]{5,30}$", input_str):
        return input_str
    return None


def extract_facebook_post_id(input_str: str) -> Optional[str]:
    """Extract or validate Facebook post reference."""
    if not input_str:
        return None
    input_str = input_str.strip()
    match = re.search(r"facebook\.com\/.*?\/(?:posts|videos|photos)\/([0-9]+)", input_str)
    if match:
        return match.group(1)
    return input_str if ("facebook.com" in input_str or input_str.isdigit()) else None

