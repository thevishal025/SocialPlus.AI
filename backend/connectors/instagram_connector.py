import requests
import uuid
from typing import List, Dict, Any, Optional
from backend.connectors.base_connector import BaseConnector, ConnectorResult
from backend.schemas.api_schemas import NormalizedComment
from backend.utils.helpers import extract_instagram_post_id
from backend.config import settings


class InstagramApiConnector(BaseConnector):
    """
    Official Meta Graph API integration for Instagram Professional Accounts
    (Business / Creator accounts linked to a Facebook Page).
    """

    def __init__(self, access_token: Optional[str] = None):
        super().__init__(platform="instagram", retrieval_method="api")
        self.access_token = access_token
        self.api_version = settings.META_API_VERSION

    def validate_identifier(self, identifier: str) -> bool:
        return extract_instagram_post_id(identifier) is not None

    def fetch_comments(
        self,
        identifier: str,
        max_comments: int = 200,
        access_token: Optional[str] = None,
        **kwargs
    ) -> ConnectorResult:
        token = access_token or self.access_token
        if not token or not token.strip() or token.startswith("YOUR_"):
            return ConnectorResult(
                success=False,
                platform="instagram",
                retrieval_method="api",
                status_code="not_configured",
                message=(
                    "Instagram Meta Graph API access token is not configured. "
                    "Connect an authorized Instagram Professional Account or provide a User/Page Access Token with "
                    "'instagram_basic' and 'instagram_manage_comments' permissions, or switch to 'Upload File' mode."
                ),
                limitations="Meta Graph API requires OAuth authorization for Instagram Business or Creator accounts."
            )

        post_id = extract_instagram_post_id(identifier)
        if not post_id:
            return ConnectorResult(
                success=False,
                platform="instagram",
                retrieval_method="api",
                status_code="invalid_identifier",
                message=f"Invalid Instagram post URL or Media ID: '{identifier}'."
            )

        comments: List[NormalizedComment] = []
        metadata: Dict[str, Any] = {"media_id": post_id}

        url = f"https://graph.facebook.com/{self.api_version}/{post_id}/comments"
        params = {
            "fields": "id,text,timestamp,username,like_count,replies{id,text,timestamp,username}",
            "limit": min(50, max_comments),
            "access_token": token
        }

        retrieved = 0
        next_url = None

        while retrieved < max_comments:
            try:
                if next_url:
                    res = requests.get(next_url, timeout=15)
                else:
                    res = requests.get(url, params=params, timeout=15)

                if res.status_code != 200:
                    err = res.json().get("error", {})
                    return ConnectorResult(
                        success=False,
                        platform="instagram",
                        retrieval_method="api",
                        status_code="api_error",
                        message=f"Meta Graph API error ({err.get('code', res.status_code)}): {err.get('message', res.text)}",
                        metadata=metadata
                    )

                data = res.json()
                items = data.get("data", [])
                if not items:
                    break

                for item in items:
                    c_id = item.get("id") or str(uuid.uuid4())
                    text = item.get("text", "")
                    if text:
                        comments.append(NormalizedComment(
                            id=c_id,
                            platform="instagram",
                            source="api",
                            author=item.get("username", "Anonymous"),
                            text=text,
                            date=item.get("timestamp"),
                            likes=item.get("like_count", 0),
                            metadata={"media_id": post_id}
                        ))
                        retrieved += 1

                    # Replies
                    replies = item.get("replies", {}).get("data", [])
                    for rep in replies:
                        if retrieved >= max_comments:
                            break
                        rep_text = rep.get("text", "")
                        if rep_text:
                            comments.append(NormalizedComment(
                                id=rep.get("id") or str(uuid.uuid4()),
                                platform="instagram",
                                source="api",
                                author=rep.get("username", "Anonymous"),
                                text=rep_text,
                                date=rep.get("timestamp"),
                                likes=0,
                                metadata={"media_id": post_id, "parent_id": c_id, "is_reply": True}
                            ))
                            retrieved += 1

                next_url = data.get("paging", {}).get("next")
                if not next_url:
                    break

            except Exception as e:
                return ConnectorResult(
                    success=False,
                    platform="instagram",
                    retrieval_method="api",
                    status_code="network_error",
                    message=f"Connection failure to Instagram Graph API: {str(e)}",
                    metadata=metadata
                )

        return ConnectorResult(
            success=True,
            platform="instagram",
            retrieval_method="api",
            status_code="success" if comments else "empty",
            message=f"Successfully fetched {len(comments)} comments from Instagram." if comments else "No comments found on this post.",
            comments=comments,
            total_found=len(comments),
            retrieved_count=len(comments),
            metadata=metadata
        )


class InstagramPublicConnector(BaseConnector):
    """
    Instagram Public Connector.
    Adheres strictly to automated access policies.
    """

    def __init__(self):
        super().__init__(platform="instagram", retrieval_method="public")

    def validate_identifier(self, identifier: str) -> bool:
        return extract_instagram_post_id(identifier) is not None

    def fetch_comments(
        self,
        identifier: str,
        max_comments: int = 200,
        **kwargs
    ) -> ConnectorResult:
        post_id = extract_instagram_post_id(identifier)
        if not post_id:
            return ConnectorResult(
                success=False,
                platform="instagram",
                retrieval_method="public",
                status_code="invalid_identifier",
                message=f"Invalid Instagram post URL: '{identifier}'."
            )

        # In accordance with Meta / Instagram Platform Terms and automated access boundaries:
        # Instagram requires user login and enforces stringent anti-bot / rate-limit protections.
        # As instructed in the master specification:
        # "When data cannot legally or technically be accessed, show:
        # 'Direct comment retrieval is unavailable for this source. Connect an authorized account or upload a comments file.'"
        return ConnectorResult(
            success=False,
            platform="instagram",
            retrieval_method="public",
            status_code="unsupported",
            message=(
                "Direct comment retrieval is unavailable for this source. "
                "Instagram enforces strict login-wall protections. "
                "Connect an authorized Instagram Professional account via the 'With API' tab or "
                "upload a comments file (CSV, Excel, JSON) using 'Upload File' mode."
            ),
            comments=[],
            total_found=0,
            retrieved_count=0,
            metadata={"shortcode": post_id},
            limitations="Instagram comments are gated behind authentication."
        )

