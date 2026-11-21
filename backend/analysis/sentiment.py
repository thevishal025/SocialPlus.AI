import re
from typing import Dict, Any, Tuple, List

# Comprehensive Multilingual Lexicons (English, Hindi, Hinglish)
POSITIVE_WORDS = {
    # English
    "great", "excellent", "good", "amazing", "awesome", "fantastic", "love", "loved", "loving",
    "best", "perfect", "superb", "brilliant", "outstanding", "wonderful", "satisfied", "helpful",
    "happy", "recommend", "recommended", "pleased", "impressive", "flawless", "favorite",
    "value", "top", "worth", "smooth", "clear", "crisp", "fast", "reliable", "solid",
    # Hindi / Hinglish
    "accha", "achha", "bahut", "badiya", "badhiya", "mast", "shandar", "zabardast", "lajawab",
    "kamaal", "kamal", "pyara", "sundar", "gazab", "dhamaal", "jhakaas", "sahi", "badhia",
    "best", "super", "hit", "shandar", "shukriya", "dhanyawad"
}

NEGATIVE_WORDS = {
    # English
    "bad", "worst", "terrible", "horrible", "awful", "poor", "hate", "hated", "disappointed",
    "disappointing", "waste", "useless", "broken", "cheap", "scam", "fraud", "regret", "slow",
    "pathetic", "defect", "defective", "faulty", "failed", "garbage", "trash", "crap",
    "overpriced", "annoying", "struggling", "freeze", "crash", "stuck", "lag", "dull",
    # Hindi / Hinglish
    "kharab", "bekar", "bakwas", "ghatiya", "kachra", "fraud", "dhoka", "lut", "barbad",
    "paisa", "bekaar", "faltu", "problem", "dikkat", "pareshan", "bura", "ganda", "loot", "nuksan"
}

SARCASM_SIGNALS = [
    r"yeah\s+right",
    r"best\s+.*\s+(if\s+you\s+like|when\s+it\s+breaks|ever\s+broken)",
    r"great\s+job\s+breaking",
    r"thanks\s+for\s+nothing",
    r"as\s+expected\s+from\s+them",
    r"masterpiece\s+of\s+failure",
    r"so\s+called\s+(expert|pro|flagship|best)",
    r"worked\s+for\s+(5|10|2|1)\s+(minutes|hours|days)",
    r"\"great\"",
    r"\"best\"",
    r"\"premium\""
]

CONTRAST_CONJUNCTIONS = {"but", "however", "although", "though", "yet", "still", "except", "lekin", "magar", "parantu"}


class SentimentAnalyzer:
    """
    Multilingual Sentiment Intelligence Engine.
    Categorizes comments into 5 mutually exclusive classes:
    - Positive
    - Negative
    - Neutral
    - Mixed
    - Sarcastic
    """

    def analyze(self, text: str, rating: float = None) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "label": "Neutral",
                "confidence": 0.50,
                "signals": ["Empty or whitespace content"]
            }

        text_lower = text.lower()
        signals = []

        # 1. Check for Sarcasm Signals
        for pattern in SARCASM_SIGNALS:
            if re.search(pattern, text_lower):
                signals.append(f"Sarcasm cue pattern match: '{pattern}'")
                return {
                    "label": "Sarcastic",
                    "confidence": 0.85,
                    "signals": signals
                }

        # Check sarcastic emojis (e.g., 🤡, 🙄, 🙃) paired with positive words
        sarcastic_emojis = {"🤡", "🙄", "🙃"}
        has_sarcastic_emoji = any(char in sarcastic_emojis for char in text)
        words = re.findall(r"\b[a-z0-9_]+\b", text_lower)
        pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)

        if has_sarcastic_emoji and pos_count > 0:
            signals.append("Sarcastic emoji paired with praise word")
            return {
                "label": "Sarcastic",
                "confidence": 0.82,
                "signals": signals
            }

        # 2. Check for Contrast / Mixed Sentiment
        has_contrast = any(c in words for c in CONTRAST_CONJUNCTIONS)
        if has_contrast and pos_count >= 1 and neg_count >= 1:
            signals.append(f"Contrasting sentiment detected ({pos_count} positive vs {neg_count} negative cues)")
            return {
                "label": "Mixed",
                "confidence": 0.78,
                "signals": signals
            }

        # 3. Consider Star Rating when available
        rating_bias = 0
        if rating is not None:
            if rating >= 4.0:
                rating_bias += 2
                signals.append(f"User rating {rating}/5 indicates positive satisfaction")
            elif rating <= 2.0:
                rating_bias -= 2
                signals.append(f"User rating {rating}/5 indicates negative dissatisfaction")

        # 4. Emoji Polarity Contribution
        pos_emojis = {"❤️", "😍", "🔥", "👍", "👏", "🎉", "😊", "🥰", "💯", "👌", "✨"}
        neg_emojis = {"👎", "💔", "😡", "🤬", "🤮", "💩", "😞", "😢", "😭"}
        
        pos_emoji_count = sum(text.count(e) for e in pos_emojis)
        neg_emoji_count = sum(text.count(e) for e in neg_emojis)
        if pos_emoji_count > 0:
            pos_count += min(pos_emoji_count, 3)
            signals.append(f"{pos_emoji_count} positive emoji(s)")
        if neg_emoji_count > 0:
            neg_count += min(neg_emoji_count, 3)
            signals.append(f"{neg_emoji_count} negative emoji(s)")

        total_pos = pos_count + max(0, rating_bias)
        total_neg = neg_count + max(0, -rating_bias)

        if total_pos > total_neg:
            diff = total_pos - total_neg
            confidence = min(0.98, 0.65 + (diff * 0.08))
            signals.append(f"Positive signals dominance ({total_pos} vs {total_neg})")
            return {
                "label": "Positive",
                "confidence": round(confidence, 2),
                "signals": signals
            }
        elif total_neg > total_pos:
            diff = total_neg - total_pos
            confidence = min(0.98, 0.65 + (diff * 0.08))
            signals.append(f"Negative signals dominance ({total_neg} vs {total_pos})")
            return {
                "label": "Negative",
                "confidence": round(confidence, 2),
                "signals": signals
            }
        elif total_pos > 0 and total_pos == total_neg:
            signals.append("Equal presence of positive and negative expressions")
            return {
                "label": "Mixed",
                "confidence": 0.70,
                "signals": signals
            }
        else:
            # Check question or neutral phrasing
            if "?" in text:
                signals.append("Inquiry / informational question structure")
            else:
                signals.append("Objective or factual statement without strong sentiment polarity")
            return {
                "label": "Neutral",
                "confidence": 0.62,
                "signals": signals
            }

