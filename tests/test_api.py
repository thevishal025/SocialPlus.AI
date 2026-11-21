import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "SocialPlus.ai"


def test_ecommerce_platforms_endpoint():
    res = client.get("/api/ecommerce/platforms")
    assert res.status_code == 200
    platforms = res.json().get("platforms", [])
    assert len(platforms) == 5
    keys = [p["key"] for p in platforms]
    assert "amazon" in keys and "flipkart" in keys and "meesho" in keys and "ajio" in keys and "myntra" in keys


def test_manual_analysis_endpoint():
    payload = {
        "title": "API Test Batch",
        "platform": "manual",
        "comments": [
            "Super clean audio and mic clarity!",
            "Terrible packaging, damaged on arrival."
        ]
    }
    res = client.post("/api/analysis/manual", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    analysis = data["analysis"]
    assert analysis["comment_count"] == 2
    assert "Positive" in analysis["summary"]["sentiment_distribution"]

    analysis_id = analysis["id"]

    # Test GET analysis
    get_res = client.get(f"/api/analysis/{analysis_id}")
    assert get_res.status_code == 200

    # Test GET comments paginated
    c_res = client.get(f"/api/analysis/{analysis_id}/comments?page=1&page_size=10")
    assert c_res.status_code == 200
    assert c_res.json()["total"] == 2

    # Test History Listing
    h_res = client.get("/api/history")
    assert h_res.status_code == 200
    assert h_res.json()["total"] >= 1

    # Test Reports Download
    pdf_res = client.get(f"/api/report/{analysis_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"

    html_res = client.get(f"/api/report/{analysis_id}/html")
    assert html_res.status_code == 200

    csv_res = client.get(f"/api/report/{analysis_id}/csv")
    assert csv_res.status_code == 200

    excel_res = client.get(f"/api/report/{analysis_id}/excel")
    assert excel_res.status_code == 200


def test_unsupported_public_fetch_endpoint():
    res = client.post("/api/youtube/public/fetch", json={"url_or_id": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert res.status_code == 200
    data = res.json()
    assert data["status_code"] == "unsupported"
    assert "Upload" in data["message"]

