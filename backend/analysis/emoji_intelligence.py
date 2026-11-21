from collections import Counter
from typing import List, Dict, Any
import re
try:
    import emoji as emoji_lib
except ImportError:  # requirements.txt installs emoji; fallback keeps API startup resilient.
    emoji_lib = None

EMOJI_CATEGORIES = {
    "Positive": {"❤️", "😊", "🔥", "👍", "👏", "💯", "👌", "✨", "🙌", "🥰", "🤩", "😁"},
    "Negative": {"👎", "💔", "🤮", "💩", "🤦", "🤦‍♂️", "🤦‍♀️", "📉"},
    "Anger": {"😡", "😠", "🤬", "👿", "😤"},
    "Love": {"❤️", "😍", "🥰", "😘", "💖", "💕", "💗", "💓"},
    "Sadness": {"😢", "😭", "😞", "😔", "😥", "💔"},
    "Celebration": {"🎉", "🚀", "🥳", "🍾", "🥂", "🎊"},
    "Sarcastic": {"🤡", "🙄", "🙃"}
}


class EmojiAnalyzer:
    """Extracts, categorizes, and analyzes emojis across comments."""

    def extract_emojis(self, text: str) -> List[str]:
        if not text:
            return []
        if emoji_lib is not None:
            return [char["emoji"] for char in emoji_lib.emoji_list(text)]
        # Lightweight Unicode fallback for common emoji blocks, including variation selectors.
        return re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u27BF](?:\uFE0F|[\U0001F3FB-\U0001F3FF])*", text)

    def analyze_dataset(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        emoji_counter = Counter()
        emoji_samples: Dict[str, List[str]] = {}

        for c in comments:
            text = c.get("text", "")
            found = self.extract_emojis(text)
            for em in found:
                emoji_counter[em] += 1
                if em not in emoji_samples:
                    emoji_samples[em] = []
                if len(emoji_samples[em]) < 3 and text not in emoji_samples[em]:
                    emoji_samples[em].append(text)

        total_emojis = sum(emoji_counter.values())
        top_emojis = []

        for em, count in emoji_counter.most_common(20):
            # Classify sentiment context for this emoji
            rel_sentiment = "Neutral"
            for cat, em_set in EMOJI_CATEGORIES.items():
                if em in em_set:
                    rel_sentiment = cat
                    break

            top_emojis.append({
                "emoji": em,
                "name": emoji_lib.demojize(em).strip(":") if emoji_lib is not None else f"emoji_{ord(em[0]):x}",
                "frequency": count,
                "percentage": round((count / total_emojis) * 100, 1) if total_emojis > 0 else 0,
                "related_sentiment": rel_sentiment,
                "samples": emoji_samples.get(em, [])
            })

        # Category breakdown
        category_counts = {k: 0 for k in EMOJI_CATEGORIES}
        for em, count in emoji_counter.items():
            for cat, em_set in EMOJI_CATEGORIES.items():
                if em in em_set:
                    category_counts[cat] += count

        return {
            "total_emojis_found": total_emojis,
            "unique_emojis_count": len(emoji_counter),
            "top_emojis": top_emojis,
            "category_distribution": category_counts
        }

