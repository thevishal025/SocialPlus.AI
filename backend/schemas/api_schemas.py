from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class NormalizedComment(BaseModel):
    id: str
    platform: str
    source: str  # api, public, upload, manual
    author: Optional[str] = "Anonymous"
    text: str
    date: Optional[str] = None
    likes: Optional[int] = 0
    rating: Optional[float] = None
    product: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FetchRequestYouTube(BaseModel):
    url_or_id: str
    max_comments: int = Field(default=200, ge=1, le=10000)
    include_replies: bool = True


class FetchRequestMeta(BaseModel):
    post_url_or_id: str
    max_comments: int = Field(default=200, ge=1, le=5000)
    access_token: Optional[str] = None


class FetchRequestEcommerce(BaseModel):
    platform: str
    query_or_url: str
    max_reviews: int = Field(default=100, ge=1, le=5000)


class ManualAnalysisRequest(BaseModel):
    title: Optional[str] = "Manual Comment Analysis"
    platform: str = "manual"
    raw_text: Optional[str] = None
    comments: Optional[List[str]] = None


class CommentFilterQuery(BaseModel):
    search: Optional[str] = None
    sentiment: Optional[str] = None
    emotion: Optional[str] = None
    intent: Optional[str] = None
    moderation_status: Optional[str] = None
    min_rating: Optional[float] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    sort_by: Optional[str] = "date"
    sort_desc: bool = True


class HealthResponse(BaseModel):
    status: str
    app_name: str
    youtube_api_configured: bool
    meta_api_configured: bool
    timestamp: str

