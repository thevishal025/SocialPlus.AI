import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.database import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False, index=True)  # youtube, instagram, facebook, ecommerce, manual, upload
    source_mode = Column(String(50), nullable=False)           # api, public, upload, manual
    target_identifier = Column(String(500), nullable=True)     # video URL, post ID, product query, filename
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    execution_time_sec = Column(Float, default=0.0)
    
    # JSON summaries: sentiment, emotion, intent, moderation, aspects, keywords, emojis
    summary_json = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    comments = relationship("CommentItem", back_populates="analysis", cascade="all, delete-orphan")


class CommentItem(Base):
    __tablename__ = "comment_items"

    id = Column(String(64), primary_key=True, index=True)
    analysis_id = Column(String(36), ForeignKey("analysis_runs.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    author = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    date = Column(String(50), nullable=True)
    likes = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    product = Column(String(255), nullable=True)

    # Classification fields
    sentiment = Column(String(30), nullable=False, index=True)          # Positive, Negative, Neutral, Mixed, Sarcastic
    sentiment_confidence = Column(Float, default=0.0)
    sentiment_signals = Column(JSON, nullable=True)

    primary_emotion = Column(String(30), nullable=False, index=True)    # Joy, Love, Anger, Sadness, etc.
    emotions_json = Column(JSON, nullable=True)

    intent = Column(String(50), nullable=False, index=True)             # Question, Feedback, Complaint, etc.

    spam_probability = Column(Float, default=0.0)
    toxicity_score = Column(Float, default=0.0)
    moderation_status = Column(String(30), default="Safe", index=True)  # Safe, Review Required, Suspicious, Spam, Toxic
    moderation_reasons = Column(JSON, nullable=True)

    aspects_json = Column(JSON, nullable=True)

    analysis = relationship("AnalysisRun", back_populates="comments")



class EcommerceReviewItem(Base):
    """Persistent raw e-commerce review archive, independent of analysis runs."""
    __tablename__ = "ecommerce_review_items"

    id = Column(String(64), primary_key=True, index=True)
    platform = Column(String(40), nullable=False, index=True)
    product_url = Column(String(1000), nullable=False, index=True)
    product_name = Column(String(500), nullable=True)
    review_id = Column(String(255), nullable=False)
    reviewer_name = Column(String(255), nullable=True)
    review_title = Column(String(1000), nullable=True)
    review_text = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)
    review_date = Column(String(100), nullable=True)
    verified_purchase = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    product_variant = Column(String(500), nullable=True)
    review_images = Column(JSON, nullable=True)
    source = Column(String(100), nullable=True)
    extracted_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
