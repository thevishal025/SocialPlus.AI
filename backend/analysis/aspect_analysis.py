import re
from typing import List, Dict, Any

ASPECT_DEFINITIONS = {
    "Battery & Charging": {
        "keywords": ["battery", "charging", "charger", "drain", "backup", "mah", "life", "charge", "adapter"],
        "display_name": "Battery & Power"
    },
    "Camera & Visuals": {
        "keywords": ["camera", "photo", "photos", "picture", "pictures", "lens", "video", "sensor", "portrait", "night mode"],
        "display_name": "Camera & Optics"
    },
    "Display & Screen": {
        "keywords": ["display", "screen", "amoled", "oled", "brightness", "hz", "refresh", "resolution", "panel"],
        "display_name": "Display & Screen"
    },
    "Performance & Speed": {
        "keywords": ["performance", "speed", "fast", "slow", "processor", "ram", "gaming", "lag", "smooth", "chipset"],
        "display_name": "Performance & Gaming"
    },
    "Build & Design": {
        "keywords": ["build", "design", "look", "looks", "material", "plastic", "metal", "glass", "weight", "premium", "finish"],
        "display_name": "Build & Aesthetics"
    },
    "Price & Value": {
        "keywords": ["price", "cost", "value", "money", "worth", "expensive", "budget", "affordable", "deal", "paisa"],
        "display_name": "Pricing & Value"
    },
    "Shipping & Delivery": {
        "keywords": ["delivery", "shipping", "courier", "fast delivery", "delayed", "arrived", "late delivery", "package"],
        "display_name": "Delivery & Logistics"
    },
    "Packaging": {
        "keywords": ["packaging", "box", "seal", "unboxing", "bubble wrap", "damaged box", "seal broken"],
        "display_name": "Packaging Condition"
    },
    "Sound & Audio": {
        "keywords": ["sound", "audio", "speaker", "speakers", "mic", "microphone", "bass", "volume", "loud", "clarity"],
        "display_name": "Sound & Acoustics"
    },
    "Customer Support": {
        "keywords": ["support", "service", "service center", "warranty", "replacement", "refund", "executive", "care"],
        "display_name": "Customer Support"
    }
}


class AspectAnalyzer:
    """Aspect-Based Sentiment Analysis (ABSA) dynamically extracting aspects from text."""

    def analyze_dataset(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        aspect_records: Dict[str, Dict[str, Any]] = {}

        for aspect_key, data in ASPECT_DEFINITIONS.items():
            aspect_records[aspect_key] = {
                "aspect": data["display_name"],
                "key": aspect_key,
                "mentions": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "samples_pos": [],
                "samples_neg": []
            }

        for c in comments:
            text = c.get("text", "")
            sentiment = c.get("sentiment", "Neutral")
            text_lower = text.lower()

            for aspect_key, data in ASPECT_DEFINITIONS.items():
                matched = any(re.search(rf"\b{kw}\b", text_lower) for kw in data["keywords"])
                if matched:
                    rec = aspect_records[aspect_key]
                    rec["mentions"] += 1

                    if sentiment == "Positive":
                        rec["positive"] += 1
                        if len(rec["samples_pos"]) < 2 and text not in rec["samples_pos"]:
                            rec["samples_pos"].append(text)
                    elif sentiment in ("Negative", "Sarcastic"):
                        rec["negative"] += 1
                        if len(rec["samples_neg"]) < 2 and text not in rec["samples_neg"]:
                            rec["samples_neg"].append(text)
                    else:
                        rec["neutral"] += 1

        # Filter aspects with at least 1 mention and compute percentages
        active_aspects = []
        total_pos_weight = 0
        total_eval_mentions = 0

        for key, rec in aspect_records.items():
            if rec["mentions"] > 0:
                m = rec["mentions"]
                pos_pct = round((rec["positive"] / m) * 100, 1)
                neg_pct = round((rec["negative"] / m) * 100, 1)
                neu_pct = round((rec["neutral"] / m) * 100, 1)

                active_aspects.append({
                    "aspect": rec["aspect"],
                    "key": key,
                    "mentions": m,
                    "positive_pct": pos_pct,
                    "negative_pct": neg_pct,
                    "neutral_pct": neu_pct,
                    "sample_positive": rec["samples_pos"][0] if rec["samples_pos"] else None,
                    "sample_negative": rec["samples_neg"][0] if rec["samples_neg"] else None
                })
                total_pos_weight += rec["positive"]
                total_eval_mentions += m

        # Sort by mentions
        active_aspects.sort(key=lambda x: x["mentions"], reverse=True)

        overall_satisfaction = (
            round((total_pos_weight / total_eval_mentions) * 100, 1)
            if total_eval_mentions > 0
            else 75.0
        )

        return {
            "aspects": active_aspects,
            "overall_satisfaction_score": overall_satisfaction,
            "aspects_count": len(active_aspects)
        }

