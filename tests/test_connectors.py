import os
import tempfile
import json
import pandas as pd
from backend.utils.helpers import (
    extract_youtube_video_id,
    extract_instagram_post_id,
    extract_facebook_post_id
)
from backend.utils.security import is_safe_url
from backend.connectors.youtube_connector import YouTubeApiConnector, YouTubePublicConnector
from backend.connectors.instagram_connector import InstagramApiConnector, InstagramPublicConnector
from backend.connectors.facebook_connector import FacebookApiConnector, FacebookPublicConnector
from backend.connectors.ecommerce_connector import EcommerceConnector
from backend.connectors.file_parser import parse_comments_file, detect_columns


def test_youtube_video_id_extraction():
    urls = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ")
    ]
    for url, expected in urls:
        assert extract_youtube_video_id(url) == expected


def test_instagram_and_facebook_identifiers():
    assert extract_instagram_post_id("https://www.instagram.com/p/C6xyz123/") == "C6xyz123"
    assert extract_facebook_post_id("https://facebook.com/12345/posts/987654321") is not None


def test_security_ssrf_validation():
    # Localhost, private IPs should be blocked
    safe, err = is_safe_url("http://127.0.0.1:8000/admin")
    assert not safe
    safe, err = is_safe_url("http://localhost/secret")
    assert not safe


def test_unconfigured_api_connectors():
    yt = YouTubeApiConnector(api_key="")
    res = yt.fetch_comments("dQw4w9WgXcQ")
    assert res.status_code == "not_configured"

    ig = InstagramApiConnector(access_token="")
    res = ig.fetch_comments("C6xyz123")
    assert res.status_code == "not_configured"

    fb = FacebookApiConnector(access_token="")
    res = fb.fetch_comments("123456789")
    assert res.status_code == "not_configured"


def test_ecommerce_registry():
    ecom = EcommerceConnector()
    platforms = ecom.get_supported_platforms()
    assert len(platforms) == 9
    platform_keys = [p["key"] for p in platforms]
    assert "amazon_in" in platform_keys
    assert "flipkart" in platform_keys
    assert "myntra" in platform_keys


def test_file_parsing_csv():
    df = pd.DataFrame({
        "User": ["Alice", "Bob"],
        "Comment": ["Love the battery backup!", "Camera is poor."],
        "Rating": [5, 2]
    })
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_csv = f.name

    try:
        comments, meta = parse_comments_file(temp_csv, "test.csv")
        assert len(comments) == 2
        assert comments[0].text == "Love the battery backup!"
        assert comments[0].rating == 5.0
        assert comments[0].author == "Alice"
    finally:
        os.remove(temp_csv)


def test_file_parsing_json():
    data = [
        {"author": "Charlie", "review": "Super fast delivery!", "score": 4.5}
    ]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump(data, f)
        temp_json = f.name

    try:
        comments, meta = parse_comments_file(temp_json, "test.json")
        assert len(comments) == 1
        assert comments[0].text == "Super fast delivery!"
        assert comments[0].rating == 4.5
    finally:
        os.remove(temp_json)

