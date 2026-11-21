import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.db_models import AnalysisRun, CommentItem


class HistoryService:
    """Manages persistence of analysis runs and individual comment records."""

    @staticmethod
    def save_analysis(db: Session, result: Dict[str, Any]) -> AnalysisRun:
        run = AnalysisRun(
            id=result["id"],
            title=result["title"],
            platform=result["platform"],
            source_mode=result["source_mode"],
            target_identifier=result.get("target_identifier"),
            comment_count=result["comment_count"],
            execution_time_sec=result.get("execution_time_sec", 0.0),
            summary_json={
                "summary": result["summary"],
                "emojis": result.get("emojis"),
                "keywords": result.get("keywords"),
                "aspects": result.get("aspects")
            },
            metadata_json=result.get("metadata", {})
        )
        db.add(run)

        # Bulk save comment items
        for c in result.get("comments", []):
            item = CommentItem(
                id=f"{run.id}_{c['id']}",
                analysis_id=run.id,
                platform=c["platform"],
                author=c.get("author"),
                text=c["text"],
                date=c.get("date"),
                likes=c.get("likes", 0),
                rating=c.get("rating"),
                product=c.get("product"),
                sentiment=c["sentiment"],
                sentiment_confidence=c.get("sentiment_confidence", 0.0),
                sentiment_signals=c.get("sentiment_signals", []),
                primary_emotion=c.get("primary_emotion", "Neutral"),
                emotions_json=c.get("emotions", {}),
                intent=c.get("intent", "General Feedback"),
                spam_probability=c.get("spam_probability", 0.0),
                toxicity_score=c.get("toxicity_score", 0.0),
                moderation_status=c.get("moderation_status", "Safe"),
                moderation_reasons=c.get("moderation_reasons", [])
            )
            db.add(item)

        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def list_history(
        db: Session,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = db.query(AnalysisRun)
        if search:
            query = query.filter(AnalysisRun.title.ilike(f"%{search}%") | AnalysisRun.platform.ilike(f"%{search}%"))
        
        runs = query.order_by(AnalysisRun.created_at.desc()).offset(offset).limit(limit).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "platform": r.platform,
                "source_mode": r.source_mode,
                "target_identifier": r.target_identifier,
                "comment_count": r.comment_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "execution_time_sec": r.execution_time_sec,
                "summary": r.summary_json.get("summary") if r.summary_json else None
            }
            for r in runs
        ]

    @staticmethod
    def get_analysis(db: Session, analysis_id: str) -> Optional[Dict[str, Any]]:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
        if not run:
            return None

        # Reconstruct full result
        summary_data = run.summary_json or {}
        comments = db.query(CommentItem).filter(CommentItem.analysis_id == analysis_id).all()

        return {
            "id": run.id,
            "title": run.title,
            "platform": run.platform,
            "source_mode": run.source_mode,
            "target_identifier": run.target_identifier,
            "comment_count": run.comment_count,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "execution_time_sec": run.execution_time_sec,
            "summary": summary_data.get("summary", {}),
            "emojis": summary_data.get("emojis", {}),
            "keywords": summary_data.get("keywords", {}),
            "aspects": summary_data.get("aspects", {}),
            "metadata": run.metadata_json or {},
            "comments": [
                {
                    "id": c.id,
                    "platform": c.platform,
                    "author": c.author,
                    "text": c.text,
                    "date": c.date,
                    "likes": c.likes,
                    "rating": c.rating,
                    "product": c.product,
                    "sentiment": c.sentiment,
                    "sentiment_confidence": c.sentiment_confidence,
                    "sentiment_signals": c.sentiment_signals,
                    "primary_emotion": c.primary_emotion,
                    "emotions": c.emotions_json,
                    "intent": c.intent,
                    "spam_probability": c.spam_probability,
                    "toxicity_score": c.toxicity_score,
                    "moderation_status": c.moderation_status,
                    "moderation_reasons": c.moderation_reasons
                }
                for c in comments
            ]
        }

    @staticmethod
    def filter_comments(
        db: Session,
        analysis_id: str,
        search: Optional[str] = None,
        sentiment: Optional[str] = None,
        emotion: Optional[str] = None,
        intent: Optional[str] = None,
        moderation_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
        sort_by: str = "date",
        sort_desc: bool = True
    ) -> Dict[str, Any]:
        query = db.query(CommentItem).filter(CommentItem.analysis_id == analysis_id)

        if search:
            query = query.filter(CommentItem.text.ilike(f"%{search}%") | CommentItem.author.ilike(f"%{search}%"))
        if sentiment and sentiment.lower() != "all":
            query = query.filter(CommentItem.sentiment == sentiment)
        if emotion and emotion.lower() != "all":
            query = query.filter(CommentItem.primary_emotion == emotion)
        if intent and intent.lower() != "all":
            query = query.filter(CommentItem.intent == intent)
        if moderation_status and moderation_status.lower() != "all":
            query = query.filter(CommentItem.moderation_status == moderation_status)

        total = query.count()

        # Sorting
        if sort_by == "likes":
            query = query.order_by(CommentItem.likes.desc() if sort_desc else CommentItem.likes.asc())
        elif sort_by == "rating":
            query = query.order_by(CommentItem.rating.desc() if sort_desc else CommentItem.rating.asc())
        elif sort_by == "confidence":
            query = query.order_by(CommentItem.sentiment_confidence.desc() if sort_desc else CommentItem.sentiment_confidence.asc())
        else:
            query = query.order_by(CommentItem.id.desc() if sort_desc else CommentItem.id.asc())

        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
            "items": [
                {
                    "id": c.id,
                    "platform": c.platform,
                    "author": c.author,
                    "text": c.text,
                    "date": c.date,
                    "likes": c.likes,
                    "rating": c.rating,
                    "sentiment": c.sentiment,
                    "sentiment_confidence": c.sentiment_confidence,
                    "sentiment_signals": c.sentiment_signals,
                    "primary_emotion": c.primary_emotion,
                    "intent": c.intent,
                    "spam_probability": c.spam_probability,
                    "toxicity_score": c.toxicity_score,
                    "moderation_status": c.moderation_status,
                    "moderation_reasons": c.moderation_reasons
                }
                for c in items
            ]
        }

    @staticmethod
    def delete_analysis(db: Session, analysis_id: str) -> bool:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id).first()
        if not run:
            return False
        db.delete(run)
        db.commit()
        return True

