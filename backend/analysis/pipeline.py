import time
import uuid
from typing import List, Dict, Any, Optional
from backend.schemas.api_schemas import NormalizedComment
from backend.analysis.sentiment import SentimentAnalyzer
from backend.analysis.emotion import EmotionAnalyzer
from backend.analysis.intent import IntentAnalyzer
from backend.analysis.moderation import ModerationAnalyzer
from backend.analysis.emoji_intelligence import EmojiAnalyzer
from backend.analysis.keywords import KeywordAnalyzer
from backend.analysis.aspect_analysis import AspectAnalyzer


class AnalysisPipeline:
    """
    Unified AI/ML Analysis Pipeline:
    All comments from any source (YouTube, Meta, E-commerce, Upload, Manual)
    are processed through this unified pipeline.
    """

    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.emotion_analyzer = EmotionAnalyzer()
        self.intent_analyzer = IntentAnalyzer()
        self.moderation_analyzer = ModerationAnalyzer()
        self.emoji_analyzer = EmojiAnalyzer()
        self.keyword_analyzer = KeywordAnalyzer()
        self.aspect_analyzer = AspectAnalyzer()

    def process_comments(
        self,
        comments: List[NormalizedComment],
        title: str = "Comment Intelligence Analysis",
        platform: str = "generic",
        source_mode: str = "upload",
        target_identifier: Optional[str] = None,
        source_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        analysis_id = str(uuid.uuid4())
        total = len(comments)

        if total == 0:
            return {
                "id": analysis_id,
                "title": title,
                "platform": platform,
                "source_mode": source_mode,
                "target_identifier": target_identifier,
                "comment_count": 0,
                "execution_time_sec": 0.0,
                "summary": {
                    "total_analyzed": 0,
                    "sentiment_distribution": {
                        "Positive": 0.0, "Negative": 0.0, "Neutral": 0.0, "Mixed": 0.0, "Sarcastic": 0.0
                    },
                    "emotion_distribution": {},
                    "intent_distribution": {},
                    "moderation_distribution": {"Safe": 0, "Review Required": 0, "Suspicious": 0, "Spam": 0, "Toxic": 0},
                    "average_confidence": 0.0,
                    "average_rating": None
                },
                "comments": [],
                "metadata": source_metadata or {}
            }

        processed_comments = []
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0, "Mixed": 0, "Sarcastic": 0}
        emotion_counts: Dict[str, int] = {}
        intent_counts: Dict[str, int] = {}
        moderation_counts = {"Safe": 0, "Review Required": 0, "Suspicious": 0, "Spam": 0, "Toxic": 0}

        confidences = []
        ratings = []

        for c in comments:
            text = c.text
            # 1. Sentiment
            sent_res = self.sentiment_analyzer.analyze(text, rating=c.rating)
            sent_label = sent_res["label"]
            sentiment_counts[sent_label] = sentiment_counts.get(sent_label, 0) + 1
            confidences.append(sent_res["confidence"])

            # 2. Emotion
            emo_res = self.emotion_analyzer.analyze(text)
            prim_emo = emo_res["primary_emotion"]
            emotion_counts[prim_emo] = emotion_counts.get(prim_emo, 0) + 1

            # 3. Intent
            intent_res = self.intent_analyzer.analyze(text)
            intent_counts[intent_res["intent"]] = intent_counts.get(intent_res["intent"], 0) + 1

            # 4. Moderation
            mod_res = self.moderation_analyzer.analyze(text)
            mod_status = mod_res["moderation_status"]
            moderation_counts[mod_status] = moderation_counts.get(mod_status, 0) + 1

            if c.rating is not None:
                ratings.append(c.rating)

            processed_comments.append({
                "id": c.id,
                "analysis_id": analysis_id,
                "platform": c.platform or platform,
                "source": c.source or source_mode,
                "author": c.author or "Anonymous",
                "text": text,
                "date": c.date,
                "likes": c.likes or 0,
                "rating": c.rating,
                "product": c.product,
                "sentiment": sent_label,
                "sentiment_confidence": sent_res["confidence"],
                "sentiment_signals": sent_res["signals"],
                "primary_emotion": prim_emo,
                "emotions": emo_res["scores"],
                "intent": intent_res["intent"],
                "spam_probability": mod_res["spam_probability"],
                "toxicity_score": mod_res["toxicity_score"],
                "moderation_status": mod_status,
                "moderation_reasons": mod_res["reasons"]
            })

        # Calculate exact mutually exclusive sentiment percentages summing to 100%
        sent_pct = {}
        raw_pcts = {k: (v / total) * 100 for k, v in sentiment_counts.items()}
        # Normalize to 100% rounding
        for k in sent_pct:
            pass
        sum_rounded = sum(round(pct, 1) for pct in raw_pcts.values())
        diff = round(100.0 - sum_rounded, 1)
        
        for k, v in raw_pcts.items():
            sent_pct[k] = round(v, 1)
        # Apply remainder rounding to highest category if needed
        if diff != 0.0:
            top_cat = max(sent_pct.items(), key=lambda x: x[1])[0]
            sent_pct[top_cat] = round(sent_pct[top_cat] + diff, 1)

        # Emotion percentages
        emotion_distribution = {
            k: {
                "count": v,
                "percentage": round((v / total) * 100, 1)
            }
            for k, v in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
        }

        # Intent percentages
        intent_distribution = {
            k: {
                "count": v,
                "percentage": round((v / total) * 100, 1)
            }
            for k, v in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
        }

        # 5. Emoji Analysis across dataset
        emoji_insights = self.emoji_analyzer.analyze_dataset(processed_comments)

        # 6. Keyword and Phrases Analysis
        keyword_insights = self.keyword_analyzer.analyze_dataset(processed_comments)

        # 7. Aspect Intelligence Analysis
        aspect_insights = self.aspect_analyzer.analyze_dataset(processed_comments)

        execution_time = round(time.time() - start_time, 2)
        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

        summary = {
            "total_retrieved": total,
            "total_analyzed": total,
            "sentiment_counts": sentiment_counts,
            "sentiment_distribution": sent_pct,
            "emotion_distribution": emotion_distribution,
            "intent_distribution": intent_distribution,
            "moderation_distribution": moderation_counts,
            "average_confidence": avg_confidence,
            "average_rating": avg_rating,
            "emoji_summary": {
                "total_emojis": emoji_insights["total_emojis_found"],
                "unique_emojis": emoji_insights["unique_emojis_count"]
            },
            "aspect_summary": {
                "aspects_count": aspect_insights["aspects_count"],
                "satisfaction_score": aspect_insights["overall_satisfaction_score"]
            }
        }

        return {
            "id": analysis_id,
            "title": title,
            "platform": platform,
            "source_mode": source_mode,
            "target_identifier": target_identifier,
            "comment_count": total,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execution_time_sec": execution_time,
            "summary": summary,
            "emojis": emoji_insights,
            "keywords": keyword_insights,
            "aspects": aspect_insights,
            "comments": processed_comments,
            "metadata": source_metadata or {}
        }


# Singleton pipeline
pipeline = AnalysisPipeline()

