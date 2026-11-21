"""
YouTube API routes with SSE progress streaming.
"""
import asyncio
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.api_schemas import FetchRequestYouTube
from backend.connectors.youtube_connector import YouTubeApiConnector, YouTubePublicConnector
from backend.analysis.pipeline import pipeline
from backend.services.history_service import HistoryService

router = APIRouter(prefix="/api/youtube", tags=["YouTube"])


# ── SSE helpers ──────────────────────────────────────────────────────────────

def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── Standard (non-streaming) fetch — used by simple POST path ────────────────

@router.post("/api/fetch")
def fetch_youtube_api(req: FetchRequestYouTube, db: Session = Depends(get_db)):
    """Fetch comments via official YouTube Data API v3 and analyze them."""
    connector = YouTubeApiConnector()
    result = connector.fetch_comments(
        identifier=req.url_or_id,
        max_comments=req.max_comments,
        include_replies=req.include_replies,
    )

    if not result.success:
        return {
            "success": False,
            "status_code": result.status_code,
            "message": result.message,
            "limitations": result.limitations,
            "metadata": result.metadata,
        }

    video_title = result.metadata.get("title") or f"YouTube Video ({req.url_or_id})"
    analysis = pipeline.process_comments(
        comments=result.comments,
        title=video_title,
        platform="youtube",
        source_mode="api",
        target_identifier=req.url_or_id,
        source_metadata=result.metadata,
    )

    HistoryService.save_analysis(db, analysis)
    return {
        "success": True,
        "status_code": "success",
        "message": result.message,
        "analysis": analysis,
    }


# ── SSE streaming fetch ───────────────────────────────────────────────────────

@router.get("/api/fetch-stream")
async def fetch_youtube_api_stream(
    url_or_id: str,
    max_comments: int = 200,
    include_replies: bool = True,
    db: Session = Depends(get_db),
):
    """
    Server-Sent Events endpoint for YouTube API fetch with progress updates.
    Client connects via EventSource; each stage fires a named event.
    """

    async def event_generator():
        yield _sse("progress", {"stage": "validating", "message": "Validating video URL…", "count": 0})
        await asyncio.sleep(0)

        connector = YouTubeApiConnector()

        if not connector.api_key or not connector.api_key.strip() or connector.api_key.startswith("YOUR_"):
            yield _sse("error", {
                "status_code": "not_configured",
                "message": "YouTube API Key is not configured. Add YOUTUBE_API_KEY to .env.",
            })
            return

        from backend.utils.helpers import extract_youtube_video_id
        video_id = extract_youtube_video_id(url_or_id)
        if not video_id:
            yield _sse("error", {
                "status_code": "invalid_identifier",
                "message": f"Invalid YouTube URL or Video ID: '{url_or_id}'.",
            })
            return

        yield _sse("progress", {"stage": "metadata", "message": "Fetching video metadata…", "count": 0})
        await asyncio.sleep(0)

        import httpx, uuid
        from backend.schemas.api_schemas import NormalizedComment

        YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
        video_metadata = {"video_id": video_id}
        comments = []
        seen_ids: set = set()

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                # Metadata
                try:
                    resp = await client.get(
                        f"{YOUTUBE_API_BASE}/videos",
                        params={"part": "snippet,statistics", "id": video_id, "key": connector.api_key},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("items", [])
                        if items:
                            snippet = items[0].get("snippet", {})
                            stats = items[0].get("statistics", {})
                            video_metadata.update({
                                "title": snippet.get("title", ""),
                                "channel_title": snippet.get("channelTitle", ""),
                                "published_at": snippet.get("publishedAt", ""),
                                "view_count": int(stats.get("viewCount", 0)),
                                "like_count": int(stats.get("likeCount", 0)),
                                "api_comment_count": int(stats.get("commentCount", 0)),
                            })
                        else:
                            yield _sse("error", {"status_code": "not_found", "message": "Video not found or private."})
                            return
                    elif resp.status_code == 403:
                        err = resp.json().get("error", {})
                        reasons = [e.get("reason") for e in err.get("errors", [])]
                        code = "quota_exceeded" if "quotaExceeded" in reasons else "api_error"
                        yield _sse("error", {"status_code": code, "message": err.get("message", "API error")})
                        return
                except httpx.TimeoutException:
                    yield _sse("error", {"status_code": "network_error", "message": "Timed out fetching video metadata."})
                    return

                yield _sse("progress", {
                    "stage": "fetching",
                    "message": f"Fetching comments for: {video_metadata.get('title', video_id)}…",
                    "count": 0,
                    "metadata": video_metadata,
                })
                await asyncio.sleep(0)

                # Comment pages
                next_page_token = None
                page_num = 0

                while len(comments) < max_comments:
                    page_num += 1
                    remaining = max_comments - len(comments)
                    page_size = min(100, remaining)

                    params = {
                        "part": "snippet,replies" if include_replies else "snippet",
                        "videoId": video_id,
                        "maxResults": page_size,
                        "textFormat": "plainText",
                        "key": connector.api_key,
                    }
                    if next_page_token:
                        params["pageToken"] = next_page_token

                    try:
                        resp = await client.get(f"{YOUTUBE_API_BASE}/commentThreads", params=params)
                    except httpx.TimeoutException:
                        break
                    except Exception as exc:
                        yield _sse("error", {"status_code": "network_error", "message": str(exc)})
                        return

                    if resp.status_code != 200:
                        err_json = resp.json().get("error", {})
                        reasons = [e.get("reason") for e in err_json.get("errors", [])]
                        if "commentsDisabled" in reasons:
                            yield _sse("error", {"status_code": "comments_disabled", "message": "Comments are disabled for this video."})
                            return
                        if "quotaExceeded" in reasons:
                            break
                        yield _sse("error", {"status_code": "api_error", "message": err_json.get("message", resp.text)})
                        return

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
                            comments.append(NormalizedComment(
                                id=top_id, platform="youtube", source="api",
                                author=top.get("authorDisplayName", "Anonymous"),
                                text=text, date=top.get("publishedAt"),
                                likes=top.get("likeCount", 0),
                                metadata={"parent_id": None, "video_id": video_id},
                            ))

                        if include_replies and "replies" in item and len(comments) < max_comments:
                            for rep in item["replies"].get("comments", []):
                                rep_sn = rep.get("snippet", {})
                                rep_id = rep.get("id", str(uuid.uuid4()))
                                rep_text = rep_sn.get("textDisplay", "").strip()
                                if rep_text and rep_id not in seen_ids and len(comments) < max_comments:
                                    seen_ids.add(rep_id)
                                    comments.append(NormalizedComment(
                                        id=rep_id, platform="youtube", source="api",
                                        author=rep_sn.get("authorDisplayName", "Anonymous"),
                                        text=rep_text, date=rep_sn.get("publishedAt"),
                                        likes=rep_sn.get("likeCount", 0),
                                        metadata={"parent_id": top_id, "video_id": video_id, "is_reply": True},
                                    ))

                    yield _sse("progress", {
                        "stage": "fetching",
                        "message": f"Page {page_num} — {len(comments)} comments fetched so far…",
                        "count": len(comments),
                        "metadata": video_metadata,
                    })
                    await asyncio.sleep(0)

                    next_page_token = data.get("nextPageToken")
                    if not next_page_token:
                        break

        except Exception as exc:
            yield _sse("error", {"status_code": "unexpected_error", "message": str(exc)})
            return

        if not comments:
            yield _sse("error", {
                "status_code": "empty",
                "message": "No comments found on this video.",
                "metadata": video_metadata,
            })
            return

        yield _sse("progress", {
            "stage": "analyzing",
            "message": f"Running AI/ML analysis on {len(comments)} comments…",
            "count": len(comments),
        })
        await asyncio.sleep(0)

        video_title = video_metadata.get("title") or f"YouTube Video ({url_or_id})"

        # Run pipeline in thread to avoid blocking event loop
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(
            None,
            lambda: pipeline.process_comments(
                comments=comments,
                title=video_title,
                platform="youtube",
                source_mode="api",
                target_identifier=url_or_id,
                source_metadata=video_metadata,
            ),
        )

        # Persist
        HistoryService.save_analysis(db, analysis)

        yield _sse("done", {
            "success": True,
            "status_code": "success",
            "message": f"Successfully analyzed {len(comments)} comments.",
            "analysis": analysis,
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Public (without API) ──────────────────────────────────────────────────────

@router.post("/public/fetch")
def fetch_youtube_public(req: FetchRequestYouTube):
    """
    Permitted public connector. Reports oEmbed metadata then returns
    honest unsupported status — does not bypass any protections.
    """
    connector = YouTubePublicConnector()
    result = connector.fetch_comments(identifier=req.url_or_id, max_comments=req.max_comments)
    return {
        "success": result.success,
        "status_code": result.status_code,
        "message": result.message,
        "limitations": result.limitations,
        "metadata": result.metadata,
    }
