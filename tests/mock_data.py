"""Sample mock datasets for automated integration testing."""

MOCK_COMMENTS_TEXT = [
    "This smartphone camera is unbelievable! Crisp photos and great night mode ❤️🔥",
    "Battery stopped working in two days. Worst customer support ever, totally defective!",
    "Is it compatible with 5G networks in India? Can someone confirm?",
    "Yeah right, amazing battery lasting 10 minutes 🤡",
    "Camera is fantastic but battery life is horrible and drains super fast.",
    "Bohot badhiya phone hai, mast camera aur fast charging!",
    "Ye bilkul bakwas product hai, paisa barbad ho gaya mera.",
    "Contact on WhatsApp +18005550199 for guaranteed crypto trading profits! Click t.me/profitpool",
    "I will murder you, you ugly piece of shit",
    "Can you please make a comparison video between this and the iPhone 15?",
    "Average display quality, nothing special for this price.",
    "Amazing packaging, received parcel in 24 hours via courier."
]

MOCK_YOUTUBE_API_RESPONSE = {
    "kind": "youtube#commentThreadListResponse",
    "nextPageToken": "token123",
    "pageInfo": {"totalResults": 2, "resultsPerPage": 2},
    "items": [
        {
            "id": "c1",
            "snippet": {
                "topLevelComment": {
                    "id": "c1",
                    "snippet": {
                        "authorDisplayName": "TechEnthusiast",
                        "textDisplay": "Superb review! Very comprehensive and honest breakdown.",
                        "likeCount": 42,
                        "publishedAt": "2026-03-01T10:00:00Z"
                    }
                }
            },
            "replies": {
                "comments": [
                    {
                        "id": "c1_r1",
                        "snippet": {
                            "authorDisplayName": "Creator",
                            "textDisplay": "Thanks for watching! Glad it helped.",
                            "likeCount": 12,
                            "publishedAt": "2026-03-01T11:00:00Z"
                        }
                    }
                ]
            }
        }
    ]
}

