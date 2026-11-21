import re
from collections import Counter
from typing import List, Dict, Any, Tuple

# Comprehensive multilingual stopwords (English + Hindi/Hinglish + Social filler words)
STOPWORDS = {
    # English
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "is", "was", "are", "were", "been", "be", "have", "has", "had", "do", "does", "did",
    "i", "me", "my", "myself", "we", "our", "you", "your", "he", "him", "she", "her",
    "it", "its", "they", "them", "their", "this", "that", "these", "those", "which",
    "who", "whom", "what", "where", "when", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "can", "will", "just", "should", "now", "also",
    "get", "got", "even", "much", "many", "really", "video", "channel", "pls", "plz",
    # Hindi / Hinglish
    "hai", "hain", "ye", "yeh", "wo", "woh", "kya", "kyun", "kaise", "kab", "kahan",
    "ko", "ki", "ka", "ke", "mein", "se", "par", "bhi", "toh", "aur", "ya", "tha",
    "thi", "the", "kar", "kare", "karna", "raha", "rahe", "rahi", "hoga", "apne",
    "mera", "meri", "mere", "hum", "tum", "aap", "sab", "koi", "kuch", "bohot", "bahut"
}

COMPLAINT_LEXICON = {
    "broken", "damaged", "stopped", "working", "heating", "battery", "drain", "refund",
    "worst", "poor", "lag", "crash", "stuck", "useless", "fraud", "waste", "defective"
}

PRODUCT_TERMS = {
    "screen", "camera", "battery", "charger", "sound", "speaker", "display", "design",
    "build", "quality", "performance", "speed", "delivery", "packaging", "price",
    "software", "update", "size", "fit", "color", "material", "processor", "ram"
}


class KeywordAnalyzer:
    """Extracts ranked keywords, n-gram phrases, aspect terms, and wordcloud data."""

    def clean_and_tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        text_lower = text.lower()
        # Remove URLs and handles
        text_clean = re.sub(r"https?://\S+|@\w+|#\w+", " ", text_lower)
        # Match alphanumeric tokens
        tokens = re.findall(r"\b[a-zA-Z]{3,}\b", text_clean)
        return [t for t in tokens if t not in STOPWORDS]

    def extract_ngrams(self, tokens: List[str], n: int = 2) -> List[str]:
        if len(tokens) < n:
            return []
        return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

    def analyze_dataset(
        self,
        comments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        word_counter = Counter()
        phrase_counter = Counter()
        positive_keywords = Counter()
        negative_keywords = Counter()
        complaint_keywords = Counter()
        product_features = Counter()

        for c in comments:
            text = c.get("text", "")
            sentiment = c.get("sentiment", "Neutral")
            tokens = self.clean_and_tokenize(text)

            for token in tokens:
                word_counter[token] += 1
                
                if sentiment == "Positive":
                    positive_keywords[token] += 1
                elif sentiment in ("Negative", "Sarcastic"):
                    negative_keywords[token] += 1

                if token in COMPLAINT_LEXICON:
                    complaint_keywords[token] += 1

                if token in PRODUCT_TERMS:
                    product_features[token] += 1

            # 2-word phrases
            for phrase in self.extract_ngrams(tokens, n=2):
                phrase_counter[phrase] += 1

        # Format Top Results
        top_words = [{"word": w, "count": cnt} for w, cnt in word_counter.most_common(25)]
        top_phrases = [{"phrase": p, "count": cnt} for p, cnt in phrase_counter.most_common(15)]
        
        # Wordcloud format: list of dicts with text and value
        wordcloud_data = [{"text": w, "value": cnt} for w, cnt in word_counter.most_common(50)]

        return {
            "top_words": top_words,
            "top_phrases": top_phrases,
            "wordcloud": wordcloud_data,
            "positive_keywords": [{"word": w, "count": cnt} for w, cnt in positive_keywords.most_common(15)],
            "negative_keywords": [{"word": w, "count": cnt} for w, cnt in negative_keywords.most_common(15)],
            "complaint_keywords": [{"word": w, "count": cnt} for w, cnt in complaint_keywords.most_common(15)],
            "product_features": [{"feature": f, "mentions": cnt} for f, cnt in product_features.most_common(15)]
        }

