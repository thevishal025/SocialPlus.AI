from typing import List, Dict, Any, Tuple
from backend.ecommerce.product_extractor import ProductInfo
from backend.ecommerce.review_extractor import CustomerReview


class DataValidator:
    """
    Data completeness checker and review deduplication validator.
    Inspects product fields and evaluates completeness statuses.
    """

    @classmethod
    def evaluate_product_completeness(cls, product: ProductInfo) -> Dict[str, str]:
        """
        Evaluates completeness status of each product field.
        Status values: FOUND, PARTIAL, NOT AVAILABLE, FAILED.
        """
        statuses = {}

        # 1. Product Name
        if product.product_name and len(product.product_name) > 3:
            statuses["product_name"] = "FOUND"
        else:
            statuses["product_name"] = "FAILED"

        # 2. Brand
        if product.brand and product.brand.strip():
            statuses["brand"] = "FOUND"
        else:
            statuses["brand"] = "NOT AVAILABLE"

        # 3. Product Image
        if product.product_images and len(product.product_images) > 0:
            statuses["product_images"] = "FOUND"
        else:
            statuses["product_images"] = "NOT AVAILABLE"

        # 4. Current Price
        if product.current_price is not None and product.current_price > 0:
            statuses["current_price"] = "FOUND"
        else:
            statuses["current_price"] = "NOT AVAILABLE"

        # 5. Description
        if product.description and len(product.description) > 30:
            statuses["description"] = "FOUND"
        elif product.description:
            statuses["description"] = "PARTIAL"
        else:
            statuses["description"] = "NOT AVAILABLE"

        # 6. Specifications
        has_specs = False
        if product.specifications:
            if isinstance(product.specifications, dict):
                has_specs = len(product.specifications.get("raw", {})) > 0 or len(product.specifications) > 0
            else:
                has_specs = bool(product.specifications)
        if has_specs:
            statuses["specifications"] = "FOUND"
        else:
            statuses["specifications"] = "NOT AVAILABLE"

        # 7. Rating
        if product.rating is not None and product.rating > 0:
            statuses["rating"] = "FOUND"
        else:
            statuses["rating"] = "NOT AVAILABLE"

        # 8. Review Count
        if product.total_reviews_count is not None and product.total_reviews_count >= 0:
            statuses["total_reviews_count"] = "FOUND"
        else:
            statuses["total_reviews_count"] = "NOT AVAILABLE"

        return statuses

    @classmethod
    def deduplicate_reviews(cls, reviews: List[CustomerReview]) -> Tuple[List[CustomerReview], int]:
        """
        Deduplicates review items based on text fingerprint and reviewer.
        Returns: (unique_reviews, duplicates_count)
        """
        unique_reviews: List[CustomerReview] = []
        seen = set()
        dups = 0

        for r in reviews:
            text_snippet = (r.review_text or "").strip().lower()[:90]
            author = (r.reviewer_name or "anon").strip().lower()
            key = f"{author}::{text_snippet}"

            if not text_snippet or len(text_snippet) < 3:
                continue

            if key in seen:
                dups += 1
                continue

            seen.add(key)
            unique_reviews.append(r)

        return unique_reviews, dups
