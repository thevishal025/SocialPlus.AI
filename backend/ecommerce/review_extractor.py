import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class CustomerReview(BaseModel):
    """Normalized structured customer review record."""
    review_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reviewer_name: str = "Customer Reviewer"
    review_title: Optional[str] = None
    review_text: str
    rating: Optional[float] = None
    review_date: Optional[str] = None
    verified_purchase: bool = False
    helpful_votes: int = 0
    product_variant: Optional[str] = None
    review_images: List[str] = Field(default_factory=list)
    platform: str = "ecommerce"
    source: str = "direct_scraper"
