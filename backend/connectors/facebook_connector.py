import requests
import uuid
from typing import List, Dict, Any, Optional
from backend.connectors.base_connector import BaseConnector, ConnectorResult
from backend.schemas.api_schemas import NormalizedComment
from backend.utils.helpers import extract_facebook_post_id
from backend.config import settings


class FacebookApiConnector(BaseConnector):
    """
    Official Meta Graph API integration for Facebook Pages that the user is authorized to manage.
    Supports pages_show_list, pages_read_engagement, and pages_read_user_content permissions.
    """

    def __init__(self, access_token: Optional[str] = None):
        super().__init__(platform="facebook", retrieval_method="api")
        self.access_token = access_token
        self.api_version = settings.META_API_VERSION

    def validate_identifier(self, identifier: str) -> bool:
        return extract_facebook_post_id(identifier) is not None

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
                platform="facebook",
                retrieval_method="api",
                status_code="not_configured",
                message=(
                    "Facebook Page Access Token is not configured. "
                    "Connect an authorized Facebook Page with 'pages_read_engagement' permission, "
                    "or switch to 'Upload File' / 'Manual Input' mode."
                ),
                limitations="Official Facebook Graph API requires a Page Access Token for post comments access."
            )

        post_id = extract_facebook_post_id(identifier)
        if not post_id:
            return ConnectorResult(
                success=False,
                platform="facebook",
                retrieval_method="api",
                status_code="invalid_identifier",
                message=f"Invalid Facebook post URL or ID: '{identifier}'."
            )

        comments: List[NormalizedComment] = []
        metadata: Dict[str, Any] = {"post_id": post_id}

        url = f"https://graph.facebook.com/{self.api_version}/{post_id}/comments"
        params = {
            "fields": "id,message,created_time,like_count,from,comments{id,message,created_time,from}",
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
                        platform="facebook",
                        retrieval_method="api",
                        status_code="api_error",
                        message=f"Facebook Graph API error ({err.get('code', res.status_code)}): {err.get('message', res.text)}",
                        metadata=metadata
                    )

                data = res.json()
                items = data.get("data", [])
                if not items:
                    break

                for item in items:
                    c_id = item.get("id") or str(uuid.uuid4())
                    msg = item.get("message", "")
                    from_user = item.get("from", {}).get("name", "Facebook User")
                    if msg:
                        comments.append(NormalizedComment(
                            id=c_id,
                            platform="facebook",
                            source="api",
                            author=from_user,
                            text=msg,
                            date=item.get("created_time"),
                            likes=item.get("like_count", 0),
                            metadata={"post_id": post_id}
                        ))
                        retrieved += 1

                    # Nested comment replies
                    nested = item.get("comments", {}).get("data", [])
                    for rep in nested:
                        if retrieved >= max_comments:
                            break
                        rep_msg = rep.get("message", "")
                        if rep_msg:
                            comments.append(NormalizedComment(
                                id=rep.get("id") or str(uuid.uuid4()),
                                platform="facebook",
                                source="api",
                                author=rep.get("from", {}).get("name", "Facebook User"),
                                text=rep_msg,
                                date=rep.get("created_time"),
                                likes=0,
                                metadata={"post_id": post_id, "parent_id": c_id, "is_reply": True}
                            ))
                            retrieved += 1

                next_url = data.get("paging", {}).get("next")
                if not next_url:
                    break

            except Exception as e:
                return ConnectorResult(
                    success=False,
                    platform="facebook",
                    retrieval_method="api",
                    status_code="network_error",
                    message=f"Connection failure to Facebook Graph API: {str(e)}",
                    metadata=metadata
                )

        return ConnectorResult(
            success=True,
            platform="facebook",
            retrieval_method="api",
            status_code="success" if comments else "empty",
            message=f"Successfully retrieved {len(comments)} comments from Facebook Page." if comments else "No comments found on this post.",
            comments=comments,
            total_found=len(comments),
            retrieved_count=len(comments),
            metadata=metadata
        )


class FacebookPublicConnector(BaseConnector):
    """
    Facebook Public Connector.
    Adheres strictly to automated access policies and privacy boundaries.
    """

    def __init__(self):
        super().__init__(platform="facebook", retrieval_method="public")

    def validate_identifier(self, identifier: str) -> bool:
        return extract_facebook_post_id(identifier) is not None

    def fetch_comments(
        self,
        identifier: str,
        max_comments: int = 200,
        **kwargs
    ) -> ConnectorResult:
        post_id = extract_facebook_post_id(identifier)
        if not post_id:
            return ConnectorResult(
                success=False,
                platform="facebook",
                retrieval_method="public",
                status_code="invalid_identifier",
                message=f"Invalid Facebook post URL: '{identifier}'."
            )

        return ConnectorResult(
            success=False,
            platform="facebook",
            retrieval_method="public",
            status_code="unsupported",
            message=(
                "Direct public comment retrieval is restricted by Facebook's automated access policies and login protections. "
                "To analyze Facebook post comments, please use:\n"
                "1. 'With API' mode with an authorized Facebook Page Access Token\n"
                "2. 'Upload File' mode to upload exported comments\n"
                "3. 'Manual Input' to paste comment text directly."
            ),
            comments=[],
            total_found=0,
            retrieved_count=0,
            metadata={"post_identifier": post_id},
            limitations="Facebook requires OAuth authorization to view comment streams."
        )

