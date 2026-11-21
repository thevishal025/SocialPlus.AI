import re
from typing import Optional, List, Any
from backend.ecommerce.review_extractor import CustomerReview
from backend.schemas.api_schemas import NormalizedComment


class DataNormalizer:
    """Normalizes raw extracted price, dates, and review items into unified schemas."""

    @staticmethod
    def parse_price(raw_price: Any) -> Optional[float]:
        if raw_price is None:
            return None
        if isinstance(raw_price, (int, float)):
            return float(raw_price)

        text = str(raw_price).strip()
        # Remove currency words / prefixes that may contain dots (e.g. "Rs.", "rs.", "inr", "₹", "$")
        cleaned_text = re.sub(r"(?i)\b(?:rs\.?|inr|usd|aud|gbp)\b", "", text)
        cleaned_text = re.sub(r"[₹$€£]", "", cleaned_text).strip()

        # Extract number sequence with commas and decimals
        matches = re.findall(r"\d[\d,]*(?:\.\d+)?", cleaned_text)
        if not matches:
            return None

        num_str = matches[0].replace(",", "")
        try:
            val = float(num_str)
            return round(val, 2)
        except ValueError:
            return None

    parse_price_value = parse_price

    @staticmethod
    def to_normalized_comments(reviews: List[CustomerReview], product_name: str) -> List[NormalizedComment]:
        """Convert CustomerReview list to SocialPlus.ai NormalizedComment schema."""
        normalized = []
        for r in reviews:
            full_text = f"{r.review_title + ': ' if r.review_title else ''}{r.review_text}".strip()
            if not full_text:
                continue

            normalized.append(NormalizedComment(
                id=r.review_id,
                platform=r.platform,
                source=r.source,
                author=r.reviewer_name or "Customer Reviewer",
                text=full_text,
                date=r.review_date,
                likes=r.helpful_votes,
                rating=r.rating,
                product=product_name,
                metadata={
                    "verified_purchase": r.verified_purchase,
                    "variant": r.product_variant,
                    "review_images": r.review_images
                }
            ))
        return normalized
