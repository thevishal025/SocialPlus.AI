import os
import re
import json
import uuid
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from backend.schemas.api_schemas import NormalizedComment


COLUMN_ALIASES = {
    "text": [
        "text", "comment", "comments", "review", "reviews", "feedback", "content",
        "body", "message", "comment_text", "review_text", "user_comment", "clean_text", "description"
    ],
    "author": [
        "author", "username", "user", "name", "reviewer", "reviewer_name",
        "commenter", "user_name", "display_name", "author_name"
    ],
    "date": [
        "date", "created_at", "timestamp", "time", "posted_at", "datetime", "published_at", "review_date"
    ],
    "likes": [
        "likes", "like_count", "upvotes", "helpful", "helpful_count", "reactions"
    ],
    "rating": [
        "rating", "ratings", "stars", "score", "review_rating", "star_rating"
    ],
    "product": [
        "product", "product_name", "item", "item_name", "title", "product_title"
    ]
}


def detect_columns(columns: List[str]) -> Dict[str, Optional[str]]:
    """Automatically detect semantic mapping for columns."""
    detected = {k: None for k in COLUMN_ALIASES}
    normalized_cols = {col: re.sub(r"[^a-z0-9]", "", col.lower()) for col in columns}

    for target_field, aliases in COLUMN_ALIASES.items():
        for col_orig, col_norm in normalized_cols.items():
            for alias in aliases:
                alias_norm = re.sub(r"[^a-z0-9]", "", alias.lower())
                if col_norm == alias_norm or alias_norm in col_norm:
                    detected[target_field] = col_orig
                    break
            if detected[target_field]:
                break

    return detected


def parse_comments_file(
    file_path: str,
    original_filename: str,
    platform: str = "upload",
    custom_mapping: Optional[Dict[str, str]] = None
) -> Tuple[List[NormalizedComment], Dict[str, Any]]:
    """
    Parse uploaded files (.csv, .xlsx, .xls, .json, .txt) and return normalized comments.
    """
    ext = os.path.splitext(original_filename)[1].lower()
    comments: List[NormalizedComment] = []
    metadata: Dict[str, Any] = {
        "filename": original_filename,
        "extension": ext,
        "detected_columns": {},
        "total_rows": 0
    }

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        metadata["total_rows"] = len(lines)
        for idx, line in enumerate(lines):
            comments.append(NormalizedComment(
                id=f"txt-{idx+1}-{uuid.uuid4().hex[:6]}",
                platform=platform,
                source="upload",
                author=f"User {idx+1}",
                text=line,
                likes=0
            ))
        return comments, metadata

    # Dataframe loaders for CSV and Excel
    df = None
    if ext == ".csv":
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding="latin1")
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path)
    elif ext == ".json":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_data = json.load(f)
        
        if isinstance(raw_data, list):
            df = pd.DataFrame(raw_data)
        elif isinstance(raw_data, dict):
            # check common container keys
            for key in ("comments", "reviews", "data", "items", "results"):
                if key in raw_data and isinstance(raw_data[key], list):
                    df = pd.DataFrame(raw_data[key])
                    break
            if df is None:
                # single record or dictionary of columns
                df = pd.DataFrame([raw_data])
    else:
        raise ValueError(f"Unsupported file format '{ext}'. Please upload CSV, XLSX, XLS, JSON, or TXT.")

    if df is None or df.empty:
        return [], metadata

    metadata["total_rows"] = len(df)
    columns_list = [str(c) for c in df.columns]

    # Auto detect or use custom mapping
    detected = detect_columns(columns_list)
    if custom_mapping:
        for k, v in custom_mapping.items():
            if v and v in columns_list:
                detected[k] = v

    metadata["detected_columns"] = detected
    text_col = detected.get("text")
    
    # If no text column detected, fallback to first object/string column or first column
    if not text_col:
        text_candidates = [c for c in columns_list if df[c].dtype == object]
        text_col = text_candidates[0] if text_candidates else columns_list[0]
        detected["text"] = text_col

    author_col = detected.get("author")
    date_col = detected.get("date")
    likes_col = detected.get("likes")
    rating_col = detected.get("rating")
    product_col = detected.get("product")

    for idx, row in df.iterrows():
        raw_val = row.get(text_col)
        if pd.isna(raw_val) or not str(raw_val).strip():
            continue

        comment_text = str(raw_val).strip()
        author_val = str(row.get(author_col, "Anonymous")) if author_col and not pd.isna(row.get(author_col)) else f"User {idx+1}"
        date_val = str(row.get(date_col, "")) if date_col and not pd.isna(row.get(date_col)) else None
        
        likes_val = 0
        if likes_col and not pd.isna(row.get(likes_col)):
            try:
                likes_val = int(float(row.get(likes_col)))
            except Exception:
                likes_val = 0

        rating_val = None
        if rating_col and not pd.isna(row.get(rating_col)):
            try:
                rating_val = float(row.get(rating_col))
            except Exception:
                pass

        product_val = str(row.get(product_col, "")) if product_col and not pd.isna(row.get(product_col)) else None

        comments.append(NormalizedComment(
            id=f"up-{idx+1}-{uuid.uuid4().hex[:6]}",
            platform=platform,
            source="upload",
            author=author_val,
            text=comment_text,
            date=date_val,
            likes=likes_val,
            rating=rating_val,
            product=product_val,
            metadata={"row_index": idx}
        ))

    return comments, metadata

