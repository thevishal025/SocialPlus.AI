import re
import html
from typing import List, Tuple, Dict, Any
from backend.schemas.api_schemas import NormalizedComment
from backend.extraction.models import DataStatus


class DataQualityValidator:
    """
    Dedicated quality validation layer.
    Ensures that retrieved comments/reviews are not blank, not raw HTML fragments,
    deduplicated correctly, and meet data integrity standards.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Unescape HTML entities
        cleaned = html.unescape(text)
        # Strip HTML tags
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        # Collapse multiple spaces and newlines
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def validate_and_deduplicate(
        cls,
        raw_comments: List[NormalizedComment]
    ) -> Tuple[List[NormalizedComment], Dict[str, int], DataStatus]:
        """
        Deduplicates and cleans raw comment records.
        Returns: (valid_comments, stats_dict, data_status)
        """
        valid_records: List[NormalizedComment] = []
        seen_keys = set()
        duplicates_count = 0
        invalid_count = 0

        for c in raw_comments:
            cleaned_text = cls.clean_text(c.text)
            
            # 1. Check for empty or trivial content
            if not c.text or len(c.text.strip()) < 2:
                invalid_count += 1
                continue
            
            # 2. Check for pure HTML junk in raw content
            raw_lower = c.text.lower()
            if "<!doctype" in raw_lower or "<html" in raw_lower or "<body" in raw_lower or "<script" in raw_lower:
                invalid_count += 1
                continue

            cleaned_text = cls.clean_text(c.text)
            if not cleaned_text or len(cleaned_text) < 3:
                invalid_count += 1
                continue

            # 3. Create normalization fingerprint for deduplication
            # (Author + normalized first 80 chars of text)
            author_norm = (c.author or "anonymous").strip().lower()
            text_norm = re.sub(r"[^\w\s]", "", cleaned_text.lower())[:80].strip()
            fingerprint = f"{author_norm}::{text_norm}"

            if fingerprint in seen_keys:
                duplicates_count += 1
                continue

            seen_keys.add(fingerprint)

            # Update comment text with cleaned version
            c.text = cleaned_text
            valid_records.append(c)

        stats = {
            "total_records": len(raw_comments),
            "valid_records": len(valid_records),
            "invalid_records": invalid_count,
            "duplicates_removed": duplicates_count,
            "unique_records": len(valid_records)
        }

        if len(valid_records) > 0:
            status = DataStatus.DATA_VALIDATED
        elif len(raw_comments) > 0:
            status = DataStatus.EXTRACTION_FAILED
        else:
            status = DataStatus.PAGE_LOADED

        return valid_records, stats, status
