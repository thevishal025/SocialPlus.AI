import re
from typing import Dict, Any, List

EMOTION_LEXICON = {
    "Joy": {
        "words": {"happy", "glad", "delighted", "cheerful", "pleasure", "enjoyed", "smiling", "fun", "khush", "sukoon", "maza"},
        "emojis": {"😄", "😃", "😀", "😊", "😁", "😆", "✨"}
    },
    "Love": {
        "words": {"love", "adore", "heart", "beloved", "favorite", "favourite", "pyar", "dil", "mohabbat"},
        "emojis": {"❤️", "💖", "💕", "😍", "🥰", "😘", "💗", "💓"}
    },
    "Anger": {
        "words": {"angry", "furious", "outraged", "mad", "hate", "scam", "cheat", "rage", "gussa", "bakwas", "chor"},
        "emojis": {"😡", "😠", "🤬", "👿", "😤"}
    },
    "Sadness": {
        "words": {"sad", "unhappy", "crying", "depressed", "sorrow", "regret", "hurt", "dukhi", "dard", "rona"},
        "emojis": {"😢", "😭", "😞", "😔", "💔", "😥"}
    },
    "Surprise": {
        "words": {"surprised", "shocked", "unexpected", "astonished", "unbelievable", "wonder", "omg", "hairan", "shock"},
        "emojis": {"😲", "😮", "🤯", "😳", "😱"}
    },
    "Fear": {
        "words": {"scared", "afraid", "worried", "anxious", "risk", "danger", "warning", "caution", "dar", "khatra"},
        "emojis": {"😨", "😰", "😬", "⚠️"}
    },
    "Frustration": {
        "words": {"frustrated", "annoying", "annoyed", "irritated", "stuck", "fed up", "waste of time", "pareshan", "thak gaya"},
        "emojis": {"🤦", "🤦‍♂️", "🤦‍♀️", "🙄", "😒", "😫"}
    },
    "Disappointment": {
        "words": {"disappointed", "letdown", "underwhelming", "useless", "not worth", "ruined", "failed", "barbad", "dull"},
        "emojis": {"🙁", "☹️", "👎", "📉"}
    },
    "Excitement": {
        "words": {"excited", "can't wait", "hyped", "thrilled", "epic", "fire", "rock", "banger", "gazab", "zabardast"},
        "emojis": {"🔥", "🚀", "🎉", "🤩", "🙌", "💥"}
    },
    "Trust": {
        "words": {"reliable", "genuine", "authentic", "trust", "honest", "recommend", "verified", "bharosa", "vishwas", "sach"},
        "emojis": {"🤝", "👍", "👌", "💯", "🛡️"}
    }
}


class EmotionAnalyzer:
    """Detects multi-label independent emotion scores + primary emotion across 10 classes."""

    def analyze(self, text: str) -> Dict[str, Any]:
        if not text:
            return {"primary_emotion": "Neutral", "scores": {k: 0.0 for k in EMOTION_LEXICON}}

        text_lower = text.lower()
        words = set(re.findall(r"\b[a-z0-9_]+\b", text_lower))
        scores: Dict[str, float] = {}

        for emotion, data in EMOTION_LEXICON.items():
            word_matches = sum(1 for w in data["words"] if w in text_lower or w in words)
            emoji_matches = sum(text.count(e) for e in data["emojis"])
            
            # Weighted calculation
            raw_score = (word_matches * 0.45) + (emoji_matches * 0.55)
            scores[emotion] = round(min(1.0, raw_score), 2)

        # Identify top scoring emotion
        sorted_emotions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_emotions[0][0] if sorted_emotions[0][1] > 0.2 else "Neutral"

        return {
            "primary_emotion": primary,
            "scores": scores
        }

