from backend.analysis.sentiment import SentimentAnalyzer
from backend.analysis.emotion import EmotionAnalyzer
from backend.analysis.intent import IntentAnalyzer
from backend.analysis.moderation import ModerationAnalyzer
from backend.analysis.emoji_intelligence import EmojiAnalyzer
from backend.analysis.keywords import KeywordAnalyzer
from backend.analysis.aspect_analysis import AspectAnalyzer
from backend.analysis.pipeline import pipeline
from backend.schemas.api_schemas import NormalizedComment
from tests.mock_data import MOCK_COMMENTS_TEXT


def test_sentiment_five_categories():
    sa = SentimentAnalyzer()

    # 1. Positive
    res_pos = sa.analyze("This smartphone is amazing, superb camera quality!")
    assert res_pos["label"] == "Positive"
    assert res_pos["confidence"] > 0.6

    # 2. Negative
    res_neg = sa.analyze("Worst purchase ever, completely broken and useless.")
    assert res_neg["label"] == "Negative"

    # 3. Neutral
    res_neu = sa.analyze("The package weighs 250 grams.")
    assert res_neu["label"] == "Neutral"

    # 4. Mixed
    res_mix = sa.analyze("Camera is fantastic but battery life is horrible.")
    assert res_mix["label"] == "Mixed"

    # 5. Sarcastic
    res_sar = sa.analyze("Yeah right, amazing battery lasting 10 minutes 🤡")
    assert res_sar["label"] == "Sarcastic"


def test_multilingual_sentiment():
    sa = SentimentAnalyzer()
    # Hinglish Positive
    res1 = sa.analyze("Bohot badiya phone hai, mast chal raha hai!")
    assert res1["label"] == "Positive"

    # Hinglish Negative
    res2 = sa.analyze("Ekdum ghatiya product hai, paisa barbad.")
    assert res2["label"] == "Negative"


def test_emotion_dimensions():
    ea = EmotionAnalyzer()
    res_joy = ea.analyze("So happy with this purchase, smiling all day! 😄")
    assert res_joy["scores"]["Joy"] > 0.3

    res_love = ea.analyze("I truly love this with all my heart! ❤️")
    assert res_love["scores"]["Love"] > 0.3


def test_intent_classification():
    ia = IntentAnalyzer()
    assert ia.analyze("How do I return this item?")["intent"] == "Question"
    assert ia.analyze("What is the price of this in India?")["intent"] == "Product Inquiry"
    assert ia.analyze("The screen cracked on day one, fix this!")["intent"] == "Complaint"
    assert ia.analyze("Thank you for this wonderful review!")["intent"] == "Appreciation"


def test_moderation_rules():
    ma = ModerationAnalyzer()

    # CRITICAL TEST: Legitimate negative customer complaint MUST NOT be marked spam
    complaint = "Your product is bad. The battery stopped working in two days."
    res_complaint = ma.analyze(complaint)
    assert res_complaint["moderation_status"] != "Spam"
    assert res_complaint["spam_probability"] < 0.5

    # Praise MUST NOT be toxic or spam
    res_praise = ma.analyze("Excellent product. I love it!")
    assert res_praise["moderation_status"] == "Safe"

    # Spam Crypto solicitation
    spam_text = "Join telegram t.me/cryptopumps for guaranteed daily returns on WhatsApp!"
    res_spam = ma.analyze(spam_text)
    assert res_spam["spam_probability"] >= 0.7
    assert res_spam["moderation_status"] in ("Spam", "Suspicious")

    # Threat / Toxic
    toxic_text = "I will murder you, die in a fire"
    res_toxic = ma.analyze(toxic_text)
    assert res_toxic["toxicity_score"] >= 0.7
    assert res_toxic["moderation_status"] == "Toxic"


def test_emoji_analyzer():
    ema = EmojiAnalyzer()
    comments = [
        {"text": "Love this phone ❤️❤️ and camera 🔥"},
        {"text": "Worst experience 🤮"}
    ]
    res = ema.analyze_dataset(comments)
    assert res["total_emojis_found"] >= 3
    top_chars = [item["emoji"] for item in res["top_emojis"]]
    assert "❤️" in top_chars or "🔥" in top_chars


def test_keyword_analyzer():
    ka = KeywordAnalyzer()
    comments = [{"text": "Battery life is great. Fast charging battery!"}]
    res = ka.analyze_dataset(comments)
    words = [item["word"] for item in res["top_words"]]
    assert "battery" in words


def test_aspect_analyzer():
    aa = AspectAnalyzer()
    comments = [
        {"text": "The camera is breathtaking, but battery is bad.", "sentiment": "Mixed"},
        {"text": "Super fast delivery and packaging was solid.", "sentiment": "Positive"}
    ]
    res = aa.analyze_dataset(comments)
    aspect_keys = [a["key"] for a in res["aspects"]]
    assert "Battery & Charging" in aspect_keys or "Camera & Visuals" in aspect_keys


def test_unified_pipeline():
    normalized = [
        NormalizedComment(
            id=f"c_{i}",
            platform="youtube",
            source="upload",
            text=text
        )
        for i, text in enumerate(MOCK_COMMENTS_TEXT)
    ]
    analysis = pipeline.process_comments(
        comments=normalized,
        title="Mock Test Analysis",
        platform="youtube"
    )

    assert analysis["comment_count"] == len(MOCK_COMMENTS_TEXT)
    summary = analysis["summary"]
    sent_dist = summary["sentiment_distribution"]
    # Check that sentiment sum is exactly 100.0%
    total_pct = sum(sent_dist.values())
    assert abs(total_pct - 100.0) < 0.01
    assert "Positive" in sent_dist
    assert "Negative" in sent_dist
    assert "Sarcastic" in sent_dist

