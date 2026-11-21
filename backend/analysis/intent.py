import re
from typing import Dict, Any

INTENT_RULES = [
    {
        "intent": "Product Inquiry",
        "patterns": [
            r"\b(price|cost|how much|rate|kitne ka|kitna price|warranty|guarantee|in stock|where to buy|link to buy)\b"
        ]
    },
    {
        "intent": "Support Request",
        "patterns": [
            r"\b(help me|contact support|customer care|call me|refund|return policy|replace|tracking|order id|ticket)\b"
        ]
    },
    {
        "intent": "Complaint",
        "patterns": [
            r"\b(broken|cracked|damaged|broke|defect|defective|scam|fraud|pathetic|worst|waste of money|horrible|cheated|kachra|barbad|issue|problem|fault|fail|failed|fix this)\b"
        ]
    },
    {
        "intent": "Appreciation",
        "patterns": [
            r"\b(thank you|thanks|great job|well done|kudos|shoutout|love your|amazing work|shukriya|dhanyawad)\b",
            r"^(nice|awesome|superb|great|mast|gazab|legend)!*$"
        ]
    },
    {
        "intent": "Suggestion",
        "patterns": [
            r"\b(you should|please add|suggest|would be better|suggestion|try adding|improve this|tip)\b"
        ]
    },
    {
        "intent": "Request",
        "patterns": [
            r"\b(please make a video|can you review|cover this|upload next|please do|plz make)\b"
        ]
    },
    {
        "intent": "Promotional Comment",
        "patterns": [
            r"\b(check my channel|subscribe to my|follow my page|link in bio|discount code|dm for collab|check out my)\b"
        ]
    },
    {
        "intent": "Spam",
        "patterns": [
            r"\b(whatsapp|telegram|crypto|invest|earn \$|profit|dm me on|whatsapp number|guaranteed income)\b"
        ]
    },
    {
        "intent": "Question",
        "patterns": [
            r"\?$",
            r"^(how|what|why|when|where|who|which|is it|can i|can you|does it|will it)\b",
            r"\b(kaise|kyun|kab|kahan|kya ye|kya)\b"
        ]
    }
]


class IntentAnalyzer:
    """Classifies comment intent into 11 business and engagement categories."""

    def analyze(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"intent": "Irrelevant", "confidence": 0.5}

        text_clean = text.strip().lower()

        # Check matched intent rules
        for rule in INTENT_RULES:
            for pat in rule["patterns"]:
                if re.search(pat, text_clean):
                    return {
                        "intent": rule["intent"],
                        "confidence": 0.88,
                        "matched_rule": pat
                    }

        # Length check for irrelevant noise (e.g. single punctuation or numbers)
        if len(text_clean) < 3 and not re.search(r"[a-z0-9]", text_clean):
            return {"intent": "Irrelevant", "confidence": 0.8}

        # Default fallback is General Feedback
        return {
            "intent": "General Feedback",
            "confidence": 0.65,
            "matched_rule": "default_feedback"
        }
