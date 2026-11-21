from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from backend.schemas.api_schemas import NormalizedComment


@dataclass
class ConnectorResult:
    success: bool
    platform: str
    retrieval_method: str  # api, public, upload, manual
    status_code: str       # success, unsupported, not_configured, rate_limited, error, empty
    message: str
    comments: List[NormalizedComment] = field(default_factory=list)
    total_found: int = 0
    retrieved_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    limitations: Optional[str] = None


class BaseConnector(ABC):
    """Abstract base class for all social media and e-commerce connectors."""

    def __init__(self, platform: str, retrieval_method: str):
        self.platform = platform
        self.retrieval_method = retrieval_method

    @abstractmethod
    def validate_identifier(self, identifier: str) -> bool:
        """Validate format of the provided URL or ID."""
        pass

    @abstractmethod
    def fetch_comments(
        self,
        identifier: str,
        max_comments: int = 200,
        **kwargs
    ) -> ConnectorResult:
        """Fetch comments or reviews from source."""
        pass

