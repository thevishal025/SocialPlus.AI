"""
YouTube connectors — API (async httpx) and Public (oEmbed metadata only).
"""
import asyncio
import uuid
import httpx
from typing import List, Dict, Any, Optional
from backend.connectors.base_connector import BaseConnector, ConnectorResult
from backend.schemas.api_schemas import NormalizedComment
from backend.utils.helpers import extract_youtube_video_id
from backend.config import settings

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeApiConnector(BaseConnector):
    """Official YouTube Data API v3 integration — async httpx for speed."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(platform="youtube", retrieval_method="api")
        self.api_key = api_key if api_key is not None else settings.YOUTUBE_API_KEY

    def validate_identifier(self, identifier: str) -> bool:
        return extract_youtube_video_id(identifier) is not None

    # ------------------------------------------------------------------ #
    # Public sync entry-point that delegates to async implementation        #
    # ------------------------------------------------------------------ #
    def fetch_comments(
        self,
        identifier: str,
        max_comments: int = 200,
        include_replies: bool = True,
        **kwargs,
    ) -> ConnectorResult:
        return asyncio.run(
            self._async_fetch(identifier, max_comments, include_replies)
        )

    # ------------------------------------------------------------------ #
    # Async implementation                                                  #
    # ------------------------------------------------------------------ #
    async def _async_fetch(
        self,
        identifier: str,
        max_comments: int,
        include_replies: bool,
    ) -> ConnectorResult:
        if not self.api_key or not self.api_key.strip() or self.api_key.startswith("YOUR_"):
            return ConnectorResult(
                success=False,
                platform="youtube",
                retrieval_method="api",
                status_code="not_configured",
                message=(
                    "YouTube API Key is not configured. "
                    "Please add YOUTUBE_API_KEY to your .env file or use 'Upload File' / 'Manual Input' mode."
                ),
                limitations="Official YouTube Data API v3 requires an authorised Google Cloud API key.",
            )

        video_id = extract_youtube_video_id(identifier)
        if not video_id:
            return ConnectorResult(
                success=False,
                platform="youtube",
                retrieval_method="api",
                status_code="invalid_identifier",
                message=f"Invalid YouTube URL or Video ID: '{identifier}'.",
            )

        video_metadata: Dict[str, Any] = {"video_id": video_id}
        comments: List[NormalizedComment] = []
        seen_ids: set = set()

        async with httpx.AsyncClient(timeout=20) as client:
            # ── 1. Fetch video metadata ──────────────────────────────────
            try:
                resp = await client.get(
                    f"{YOUTUBE_API_BASE}/videos",
                    params={
                        "part": "snippet,statistics",
                        "id": video_id,
                        "key": self.api_key,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    if items:
                        snippet = items[0].get("snippet", {})
                        stats = items[0].get("statistics", {})
                        video_metadata.update(
                            {
                                "title": snippet.get("title", ""),
                                "channel_title": snippet.get("channelTitle", ""),
                                "published_at": snippet.get("publishedAt", ""),
                                "view_count": int(stats.get("viewCount", 0)),
                                "like_count": int(stats.get("likeCount", 0)),
                                "api_comment_count": int(stats.get("commentCount", 0)),
                            }
                        )
                    else:
                        return ConnectorResult(
                            success=False,
                            platform="youtube",
                            retrieval_method="api",
                            status_code="not_found",
                            message="YouTube video not found or set to private.",
                        )
                elif resp.status_code == 403:
                    err = resp.json().get("error", {})
                    reasons = [e.get("reason") for e in err.get("errors", [])]
                    if "quotaExceeded" in reasons:
                        return ConnectorResult(
                            success=False,
                            platform="youtube",
                            retrieval_method="api",
                            status_code="quota_exceeded",
                            message="YouTube API quota exceeded for today. Please wait for quota refresh.",
                        )
                    return ConnectorResult(
                        success=False,
                        platform="youtube",
                        retrieval_method="api",
                        status_code="api_error",
                        message=f"YouTube API permission error: {err.get('message', 'Forbidden')}",
                    )
                elif resp.status_code == 404:
                    return ConnectorResult(
                        success=False,
                        platform="youtube",
                        retrieval_method="api",
                        status_code="not_found",
                        message="YouTube video not found.",
                    )
            except httpx.TimeoutException:
                return ConnectorResult(
                    success=False,
                    platform="youtube",
                    retrieval_method="api",
                    status_code="network_error",
                    message="Request timed out while fetching video metadata from YouTube API.",
                )
            except Exception as exc:
                video_metadata["meta_error"] = str(exc)

            # ── 2. Fetch comment threads with pagination ─────────────────
            next_page_token: Optional[str] = None
            page_num = 0

            while len(comments) < max_comments:
                page_num += 1
                remaining = max_comments - len(comments)
                page_size = min(100, remaining)

                params: Dict[str, Any] = {
                    "part": "snippet,replies" if include_replies else "snippet",
                    "videoId": video_id,
                    "maxResults": page_size,
                    "textFormat": "plainText",
                    "key": self.api_key,
                }
                if next_page_token:
                    params["pageToken"] = next_page_token

                try:
                    resp = await client.get(
                        f"{YOUTUBE_API_BASE}/commentThreads",
                        params=params,
                    )
                except httpx.TimeoutException:
                    break
                except Exception as exc:
                    return ConnectorResult(
                        success=False,
                        platform="youtube",
                        retrieval_method="api",
                        status_code="network_error",
                        message=f"Network error while fetching comments: {exc}",
                        metadata=video_metadata,
                    )

                if resp.status_code != 200:
                    err_json = resp.json().get("error", {})
                    reasons = [e.get("reason") for e in err_json.get("errors", [])]
                    if "commentsDisabled" in reasons:
                        return ConnectorResult(
                            success=False,
                            platform="youtube",
                            retrieval_method="api",
                            status_code="comments_disabled",
                            message="Comments are disabled for this YouTube video.",
                            metadata=video_metadata,
                        )
                    if "quotaExceeded" in reasons:
                        break  # Return what we have so far
                    return ConnectorResult(
                        success=False,
                        platform="youtube",
                        retrieval_method="api",
                        status_code="api_error",
                        message=f"YouTube API error: {err_json.get('message', resp.text)}",
                        metadata=video_metadata,
                    )

                data = resp.json()
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    top = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                    top_id = item.get("id") or str(uuid.uuid4())

                    text = top.get("textDisplay", "").strip()
                    if text and top_id not in seen_ids:
                        seen_ids.add(top_id)
                        comments.append(
                            NormalizedComment(
                                id=top_id,
                                platform="youtube",
                                source="api",
                                author=top.get("authorDisplayName", "Anonymous"),
                                text=text,
                                date=top.get("publishedAt"),
                                likes=top.get("likeCount", 0),
                                metadata={"parent_id": None, "video_id": video_id},
                            )
                        )

                    # Include replies from the same batch (no extra API call)
                    if include_replies and "replies" in item and len(comments) < max_comments:
                        for rep in item["replies"].get("comments", []):
                            rep_sn = rep.get("snippet", {})
                            rep_id = rep.get("id", str(uuid.uuid4()))
                            rep_text = rep_sn.get("textDisplay", "").strip()
                            if rep_text and rep_id not in seen_ids and len(comments) < max_comments:
                                seen_ids.add(rep_id)
                                comments.append(
                                    NormalizedComment(
                                        id=rep_id,
                                        platform="youtube",
                                        source="api",
                                        author=rep_sn.get("authorDisplayName", "Anonymous"),
                                        text=rep_text,
                                        date=rep_sn.get("publishedAt"),
                                        likes=rep_sn.get("likeCount", 0),
                                        metadata={
                                            "parent_id": top_id,
                                            "video_id": video_id,
                                            "is_reply": True,
                                        },
                                    )
                                )

                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break

        if not comments:
            return ConnectorResult(
                success=True,
                platform="youtube",
                retrieval_method="api",
                status_code="empty",
                message="No comments found on this video.",
                comments=[],
                total_found=video_metadata.get("api_comment_count", 0),
                retrieved_count=0,
                metadata=video_metadata,
            )

        return ConnectorResult(
            success=True,
            platform="youtube",
            retrieval_method="api",
            status_code="success",
            message=f"Successfully fetched {len(comments)} comments via YouTube Data API v3.",
            comments=comments,
            total_found=video_metadata.get("api_comment_count", len(comments)),
            retrieved_count=len(comments),
            metadata=video_metadata,
        )


class YouTubePublicConnector(BaseConnector):
    """
    Permitted public connector — retrieves video metadata via oEmbed.
    Does NOT bypass any YouTube protections.  Returns honest status.
    """

    def __init__(self):
        super().__init__(platform="youtube", retrieval_method="public")

    def validate_identifier(self, identifier: str) -> bool:
        return extract_youtube_video_id(identifier) is not None

    def fetch_comments(
        self,
        identifier: str,
        max_comments: int = 200,
        **kwargs,
    ) -> ConnectorResult:
        video_id = extract_youtube_video_id(identifier)
        if not video_id:
            return ConnectorResult(
                success=False,
                platform="youtube",
                retrieval_method="public",
                status_code="invalid_identifier",
                message=f"Invalid YouTube URL or ID: '{identifier}'.",
            )

        metadata: Dict[str, Any] = {"video_id": video_id}

        # Fetch permitted public oEmbed data
        try:
            import requests as _req  # sync fallback for public endpoint
            oembed_url = (
                f"https://www.youtube.com/oembed"
                f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
            )
            resp = _req.get(oembed_url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                metadata["title"] = data.get("title", "")
                metadata["author_name"] = data.get("author_name", "")
                metadata["author_url"] = data.get("author_url", "")
                metadata["thumbnail_url"] = data.get("thumbnail_url", "")
            elif resp.status_code == 401:
                return ConnectorResult(
                    success=False,
                    platform="youtube",
                    retrieval_method="public",
                    status_code="access_restricted",
                    message=(
                        "This video is private or age-restricted — oEmbed returned 401. "
                        "Please use 'With API' mode or 'Upload File' to analyze."
                    ),
                    metadata=metadata,
                    limitations="Private or restricted YouTube videos cannot be accessed publicly.",
                )
            elif resp.status_code == 404:
                return ConnectorResult(
                    success=False,
                    platform="youtube",
                    retrieval_method="public",
                    status_code="not_found",
                    message="YouTube video not found (404). Verify the URL is correct.",
                    metadata=metadata,
                )
        except Exception as exc:
            metadata["oembed_error"] = str(exc)

        return ConnectorResult(
            success=False,
            platform="youtube",
            retrieval_method="public",
            status_code="unsupported",
            message=(
                "Direct automated comment extraction without an API key is blocked by YouTube's "
                "anti-bot controls and Terms of Service.\n\n"
                "Available alternatives:\n"
                "1. Switch to 'With API' mode — paste the same YouTube URL and click Fetch.\n"
                "2. Switch to 'Upload File' mode — upload an exported CSV / JSON / Excel file of comments.\n"
                "3. Use 'Manual Input' (top-right) to paste individual comments."
            ),
            comments=[],
            total_found=0,
            retrieved_count=0,
            metadata=metadata,
            limitations=(
                "YouTube enforces bot-detection, CAPTCHA challenges and login-walls on its "
                "comment sections. SocialPlus.ai does not bypass these protections."
            ),
        )
