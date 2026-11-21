import re
import json
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup

from backend.schemas.api_schemas import NormalizedComment
from backend.universal_scraper.engine import UniversalScraperEngine
from backend.utils.helpers import extract_instagram_post_id, extract_facebook_post_id


class UniversalInstagramScraper:
    """
    Universal Scraper Engine for Instagram Posts & Public Comment Threads.
    Extracts post caption, author, likes, comment count, and available comments
    using JSON-LD, OpenGraph metadata, and structured DOM parsing.
    """

    @classmethod
    def extract_shortcode(cls, url: str) -> Optional[str]:
        return extract_instagram_post_id(url)

    @classmethod
    async def extract_post_and_comments(
        cls,
        url: str,
        max_comments: int = 100,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Executes Universal Scraper for Instagram.
        Returns:
        {
            "success": bool,
            "status": str ("success" | "partial" | "login_required" | "not_found" | "error"),
            "post_metadata": { ... },
            "comments": [NormalizedComment, ...],
            "message": str
        }
        """
        shortcode = cls.extract_shortcode(url)
        if not shortcode:
            return {
                "success": False,
                "status": "not_found",
                "post_metadata": {},
                "comments": [],
                "message": f"Invalid Instagram URL or shortcode could not be extracted from '{url}'."
            }

        target_url = f"https://www.instagram.com/p/{shortcode}/"

        if progress_callback:
            await progress_callback(15, f"Fetching Instagram post {shortcode} via Universal Scraper Engine...")

        # Stage 1 & 2: Fetch Page
        fetch_res = await UniversalScraperEngine.fetch_page(
            target_url,
            force_browser=False,
            wait_selector="article, main, meta[property='og:description']",
            progress_callback=progress_callback
        )

        if not fetch_res["success"]:
            return {
                "success": False,
                "status": "error",
                "post_metadata": {},
                "comments": [],
                "message": fetch_res.get("error") or "Failed to connect to Instagram."
            }

        html = fetch_res["html"]
        soup = fetch_res["soup"]
        structured = fetch_res["structured_data"]
        og = structured.get("meta", {})
        json_lds = structured.get("json_ld", [])

        # Check for Instagram Login Wall
        is_login_wall = (
            "accounts/login" in fetch_res.get("resolved_url", "") or
            "Login • Instagram" in (soup.title.string if soup.title else "") or
            soup.select_one("form#loginForm") is not None
        )

        # ── Extract Post Metadata ──
        author = None
        caption = None
        like_count = None
        comment_count = None
        timestamp = None
        post_image = og.get("og:image") or og.get("twitter:image")

        # 1. From OpenGraph Description (Standard Instagram Format: "1,234 likes, 56 comments - user on Date: 'caption'")
        og_desc = og.get("og:description") or ""
        if og_desc:
            m_likes = re.search(r"([\d,KkMm.]+)\s+likes?", og_desc, re.IGNORECASE)
            if m_likes:
                like_str = m_likes.group(1).replace(",", "")
                try:
                    if "k" in like_str.lower():
                        like_count = int(float(like_str.lower().replace("k", "")) * 1000)
                    elif "m" in like_str.lower():
                        like_count = int(float(like_str.lower().replace("m", "")) * 1000000)
                    else:
                        like_count = int(like_str)
                except Exception:
                    pass

            m_comments = re.search(r"([\d,KkMm.]+)\s+comments?", og_desc, re.IGNORECASE)
            if m_comments:
                cmt_str = m_comments.group(1).replace(",", "")
                try:
                    if "k" in cmt_str.lower():
                        comment_count = int(float(cmt_str.lower().replace("k", "")) * 1000)
                    else:
                        comment_count = int(cmt_str)
                except Exception:
                    pass

            # Extract user & caption: "... - username on Month DD, YYYY: 'caption'"
            m_user_cap = re.search(r"-\s*([^:]+?)\s*on\s*[^:]*?:\s*[\"']?(.*)[\"']?$", og_desc)
            if m_user_cap:
                author = m_user_cap.group(1).strip()
                caption = m_user_cap.group(2).strip().rstrip("\"'")

        # 2. From OpenGraph Title: "User on Instagram: 'Caption'"
        og_title = og.get("og:title") or ""
        if not author and og_title:
            m_u = re.search(r"^([^:]+?)\s+on Instagram", og_title, re.IGNORECASE)
            if m_u:
                author = m_u.group(1).strip()

        # 3. From JSON-LD
        for j_item in json_lds:
            if not caption and j_item.get("articleBody"):
                caption = j_item["articleBody"]
            if not caption and j_item.get("caption"):
                caption = j_item["caption"]
            if not author and j_item.get("author", {}).get("name"):
                author = j_item["author"]["name"]
            if not timestamp and j_item.get("dateCreated"):
                timestamp = j_item["dateCreated"]
            if not timestamp and j_item.get("uploadDate"):
                timestamp = j_item["uploadDate"]

        post_meta = {
            "platform": "instagram",
            "post_url": target_url,
            "post_id": shortcode,
            "author": author or "Instagram User",
            "caption": caption or (og_title if og_title else "Instagram Post"),
            "post_image": post_image,
            "like_count": like_count,
            "comment_count": comment_count,
            "timestamp": timestamp or time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # ── Extract Available Comments ──
        extracted_comments: List[NormalizedComment] = []

        # Extract only structured comment objects. A generic regex over every
        # "text" field incorrectly pairs unrelated captions/usernames as comments.
        def walk_comment_nodes(value):
            if isinstance(value, dict):
                text_value = value.get("text") or value.get("comment_text")
                owner = value.get("owner") or value.get("user") or value.get("author") or {}
                username = owner.get("username") or owner.get("name") if isinstance(owner, dict) else None
                if isinstance(text_value, str) and text_value.strip() and username:
                    yield {"text": text_value.strip(), "author": username,
                           "id": value.get("id") or value.get("pk"),
                           "created_at": value.get("created_at") or value.get("created_time"),
                           "likes": value.get("comment_like_count") or value.get("like_count") or 0}
                for child in value.values():
                    yield from walk_comment_nodes(child)
            elif isinstance(value, list):
                for child in value:
                    yield from walk_comment_nodes(child)

        seen_comment_keys = set()
        for script in soup.find_all("script"):
            script_text = script.string or script.get_text() or ""
            if not script_text or not any(k in script_text for k in ("edge_media_to_parent_comment", "edge_media_to_comment", "comment_text")):
                continue
            try:
                payload = json.loads(script_text)
            except (ValueError, TypeError):
                continue
            for item in walk_comment_nodes(payload):
                key = str(item.get("id") or (item["author"] + "|" + item["text"]))
                if key in seen_comment_keys or len(extracted_comments) >= max_comments:
                    continue
                seen_comment_keys.add(key)
                extracted_comments.append(NormalizedComment(
                    id=str(item.get("id") or uuid.uuid5(uuid.NAMESPACE_URL, key)),
                    platform="instagram",
                    source="public",
                    author=item["author"],
                    text=item["text"],
                    date=str(item.get("created_at") or ""),
                    likes=int(item.get("likes") or 0),
                    metadata={"post_id": shortcode}
                ))

        # If comments extracted, return success
        if extracted_comments:
            unique_comments = UniversalScraperEngine.deduplicate_items(extracted_comments, lambda c: c.text)
            return {
                "success": True,
                "status": "success",
                "post_metadata": post_meta,
                "comments": unique_comments,
                "message": f"Successfully extracted post details and {len(unique_comments)} comments from Instagram."
            }

        # If post metadata found but comments gated behind login
        if is_login_wall or (caption or author or like_count is not None):
            return {
                "success": True,
                "status": "partial",
                "post_metadata": post_meta,
                "comments": [],
                "message": (
                    f"Extracted Instagram post details for '{shortcode}', but comment threads are protected behind "
                    "Instagram's authentication wall. Use 'With API' mode with an authorized Meta Graph Token, "
                    "or 'Upload File' mode to analyze exported comments."
                )
            }

        return {
            "success": False,
            "status": "login_required",
            "post_metadata": post_meta,
            "comments": [],
            "message": (
                "Instagram requires user authentication to access this post. "
                "Connect via 'With API' mode with an authorized account or upload a dataset in 'Upload File' mode."
            )
        }


class UniversalFacebookScraper:
    """
    Universal Scraper Engine for Facebook Posts & Public Comment Threads.
    Extracts post caption, page/author, engagement counts, and public comments.
    """

    @classmethod
    def extract_post_id(cls, url: str) -> Optional[str]:
        return extract_facebook_post_id(url)

    @classmethod
    async def extract_post_and_comments(
        cls,
        url: str,
        max_comments: int = 100,
        progress_callback=None
    ) -> Dict[str, Any]:
        post_id = cls.extract_post_id(url)
        if progress_callback:
            await progress_callback(15, f"Fetching Facebook post ({post_id or 'direct URL'}) via Universal Scraper Engine...")

        fetch_res = await UniversalScraperEngine.fetch_page(
            url,
            force_browser=False,
            wait_selector="div[role='article'], meta[property='og:description']",
            progress_callback=progress_callback
        )

        if not fetch_res["success"]:
            return {
                "success": False,
                "status": "error",
                "post_metadata": {},
                "comments": [],
                "message": fetch_res.get("error") or "Failed to connect to Facebook."
            }

        html = fetch_res["html"]
        soup = fetch_res["soup"]
        structured = fetch_res["structured_data"]
        og = structured.get("meta", {})
        json_lds = structured.get("json_ld", [])

        # Check for Facebook Login Wall
        is_login_wall = (
            "login" in fetch_res.get("resolved_url", "").lower() or
            "Log in to Facebook" in (soup.title.string if soup.title else "") or
            soup.select_one("input[name='email'], input#email") is not None
        )

        # Extract Post Metadata
        author = og.get("og:site_name") or "Facebook Page"
        caption = og.get("og:description") or og.get("og:title")
        post_image = og.get("og:image")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        for j_item in json_lds:
            if j_item.get("headline"):
                caption = j_item["headline"]
            if j_item.get("author", {}).get("name"):
                author = j_item["author"]["name"]
            if j_item.get("datePublished"):
                timestamp = j_item["datePublished"]

        post_meta = {
            "platform": "facebook",
            "post_url": url,
            "post_id": post_id or "facebook_post",
            "author": author,
            "caption": caption or "Facebook Post",
            "post_image": post_image,
            "timestamp": timestamp
        }

        # Extract available comments
        extracted_comments: List[NormalizedComment] = []
        # Only use explicit comment-body markers. Never treat every text node
        # inside a post article as a comment; that previously captured captions,
        # buttons and accessibility labels as false comments.
        comment_selectors = (
            "[data-testid='UFI2Comment/body']",
            "[data-testid='comment-body']",
            "div[aria-label='Comment']"
        )
        seen_text = set()
        for selector in comment_selectors:
            for card in soup.select(selector):
                txt = card.get_text(separator=" ", strip=True)
                if not txt or len(txt) <= 2 or txt in seen_text:
                    continue
                seen_text.add(txt)
                extracted_comments.append(NormalizedComment(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, (post_id or '') + '|' + txt)),
                    platform="facebook",
                    source="public",
                    author="Facebook User",
                    text=txt,
                    date="",
                    likes=0,
                    metadata={"post_id": post_id, "author_unavailable": True}
                ))
                if len(extracted_comments) >= max_comments:
                    break
            if len(extracted_comments) >= max_comments:
                break

        if extracted_comments:
            unique_comments = UniversalScraperEngine.deduplicate_items(extracted_comments, lambda c: c.text)
            return {
                "success": True,
                "status": "success",
                "post_metadata": post_meta,
                "comments": unique_comments,
                "message": f"Successfully extracted Facebook post details and {len(unique_comments)} comments."
            }

        if is_login_wall or caption:
            return {
                "success": True,
                "status": "partial",
                "post_metadata": post_meta,
                "comments": [],
                "message": (
                    "Extracted Facebook post details, but comments are restricted behind Facebook login wall. "
                    "Use 'With API' mode with an authorized Page Access Token or 'Upload File' mode to analyze comments."
                )
            }

        return {
            "success": False,
            "status": "login_required",
            "post_metadata": post_meta,
            "comments": [],
            "message": "Facebook login wall encountered. Please connect with an authorized Meta Page Token or upload a dataset."
        }

