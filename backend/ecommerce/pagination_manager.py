from typing import Optional


class PaginationManager:
    """Tracks accessible review pagination. None means no application-level cap."""

    def __init__(self, max_reviews: Optional[int] = None, max_pages: Optional[int] = None):
        self.max_reviews = max_reviews
        self.max_pages = max_pages
        self.current_page = 1
        self.total_extracted = 0
        self.has_next = True

    def should_continue(self) -> bool:
        if self.max_reviews is not None and self.total_extracted >= self.max_reviews:
            return False
        if self.max_pages is not None and self.current_page > self.max_pages:
            return False
        return self.has_next

    def record_page_results(self, count: int, has_more: bool = True):
        self.total_extracted += max(0, count)
        self.current_page += 1
        self.has_next = bool(has_more and count > 0)

    def remaining_needed(self) -> Optional[int]:
        if self.max_reviews is None:
            return None
        return max(0, self.max_reviews - self.total_extracted)
