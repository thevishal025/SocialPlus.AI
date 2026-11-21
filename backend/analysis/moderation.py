import re
from typing import Dict, Any, List

# Explicit toxicity patterns: Hate speech, severe profanity, personal threats
TOXIC_PATTERNS = [
    r"\b(kill yourself|go die|murder|shoot you|cut your throat)\b",
    r"\b(bitch|slut|whore|motherfucker|fucking|asshole|bastard|cunt)\b",
    r"\b(madarchod|bhenchod|chutiya|gaand|harami|kutta|randi)\b",
    r"\b(hate (all|every)\s+(jews|muslims|hindus|blacks|whites|immigrants))\b"
]

# Explicit spam patterns: crypto/financial solicitation, telegram/whatsapp recruiter bots, suspicious redirects
SPAM_PATTERNS = [
    r"\b(t\.me\/[a-zA-Z0-9_]+|telegram\s*(?:at|@|:))\b",
    r"\b(whatsapp\s*(?:me|number|\+?[\d\s-]{10,}))\b",
    r"\b(earn\s*\$?\d+[\d,]*\s*(?:daily|per day|weekly|from home))\b",
    r"\b(crypto\s*investment|forex\s*trading|binary\s*option|bitcoin\s*mining\s*pool)\b",
    r"\b(guaranteed\s*(?:returns|profit|wealth|income))\b",
    r"\b(dm\s*for\s*(?:fx|signals|dropshipping|pumps))\b"
]


class ModerationAnalyzer:
    """
    Auto-Moderation Engine:
    Independent scoring for Spam vs Toxicity vs Abuse.
    Strictly preserves customer complaints, product criticism, and legitimate inquiries as non-spam.
    """

    def analyze(self, text: str) -> Dict[str, Any]:
        if not text:
            return {
                "spam_probability": 0.0,
                "toxicity_score": 0.0,
                "abuse_indicator": False,
                "moderation_status": "Safe",
                "reasons": []
            }

        text_lower = text.lower()
        reasons = []
        spam_score = 0.0
        toxicity_score = 0.0

        # 1. Toxicity & Abuse Detection
        for pat in TOXIC_PATTERNS:
            if re.search(pat, text_lower):
                toxicity_score = max(toxicity_score, 0.85)
                reasons.append("Contains offensive language, profanity, or threatening content")
                break

        # Check for aggressive all-caps shouting (>75% uppercase with length > 20)
        letters = [c for c in text if c.isalpha()]
        if len(letters) > 20:
            upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
            if upper_ratio > 0.85:
                toxicity_score = max(toxicity_score, 0.35)
                reasons.append("High ratio of uppercase text (aggressive tone)")

        # 2. Spam Detection
        for pat in SPAM_PATTERNS:
            if re.search(pat, text_lower):
                spam_score = max(spam_score, 0.90)
                reasons.append("Matches automated financial/crypto or messaging solicitation spam patterns")
                break

        # Suspicious external links (bit.ly, tinyurl, t.co without context)
        if re.search(r"\b(bit\.ly|tinyurl\.com|goo\.gl|t\.co)\b", text_lower):
            spam_score = max(spam_score, 0.55)
            reasons.append("Contains shortened redirect URL frequently associated with link spam")

        # Repetitive characters / words (e.g. "aaaaa!!!!!", "buy now buy now buy now")
        if re.search(r"(.)\1{6,}", text):
            spam_score = max(spam_score, 0.30)
            reasons.append("Repetitive character flooding detected")

        # Determine Final Moderation Label
        if toxicity_score >= 0.70:
            status = "Toxic"
        elif spam_score >= 0.70:
            status = "Spam"
        elif toxicity_score >= 0.35 or spam_score >= 0.50:
            status = "Suspicious"
        elif toxicity_score > 0.15 or spam_score > 0.25:
            status = "Review Required"
        else:
            status = "Safe"

        return {
            "spam_probability": round(spam_score, 2),
            "toxicity_score": round(toxicity_score, 2),
            "abuse_indicator": toxicity_score >= 0.70,
            "moderation_status": status,
            "reasons": reasons if reasons else ["Content meets standard safety guidelines"]
        }

