import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.ecommerce.platform_detector import PlatformDetector
from backend.ecommerce.product_extractor import (
    ProductInfo,
    SpecificationParser
)
from backend.ecommerce.review_extractor import CustomerReview
from backend.ecommerce.pagination_manager import PaginationManager
from backend.ecommerce.data_normalizer import DataNormalizer
from backend.ecommerce.data_validator import DataValidator
from backend.ecommerce.amazon_scraper import AmazonScraper
from backend.ecommerce.flipkart_scraper import FlipkartScraper
from backend.ecommerce.meesho_scraper import MeeshoScraper
from backend.ecommerce.ajio_scraper import AjioScraper
from backend.ecommerce.myntra_scraper import MyntraScraper

client = TestClient(app)


def test_ecommerce_platforms_endpoint():
    res = client.get("/api/ecommerce/platforms")
    assert res.status_code == 200
    data = res.json()
    assert "platforms" in data
    keys = [p["key"] for p in data["platforms"]]
    assert "amazon" in keys
    assert "flipkart" in keys
    assert "meesho" in keys
    assert "ajio" in keys
    assert "myntra" in keys


def test_platform_detector():
    cases = [
        ("https://www.amazon.in/dp/B0CX24T4NQ", "amazon"),
        ("https://amazon.in/Apple-iPhone-15-128-GB/dp/B0CHX1W1XY", "amazon"),
        ("https://www.flipkart.com/motorola-g34-5g-charcoal-black-128-gb/p/itm4b76", "flipkart"),
        ("https://dl.flipkart.com/s/sample_short_id", "flipkart"),
        ("https://www.meesho.com/s/p/7t0x6p", "meesho"),
        ("https://www.ajio.com/gap-men-solid-crew-neck-t-shirt/p/460492837_blue", "ajio"),
        ("https://www.myntra.com/tshirts/roadster/roadster-men-black-cotton-pure-cotton-t-shirt/2127874/buy", "myntra"),
    ]
    for url, expected in cases:
        plat, resolved, meta, err = PlatformDetector.detect_from_url(url)
        assert plat == expected, f"Expected {expected} for {url}, got {plat}"
        assert not err


def test_platform_detector_unsupported_and_ssrf():
    # Unsupported URL
    plat, _, _, err = PlatformDetector.detect_from_url("https://www.randomshop.com/item123")
    assert plat is None
    assert "Unsupported" in err

    # SSRF / Local IP blocked
    plat, _, _, err = PlatformDetector.detect_from_url("http://127.0.0.1:8000/admin")
    assert plat is None
    assert "prohibited" in err or "Security" in err or "Blocked" in err


def test_specification_parser_category_detection():
    # Mobile
    cat = SpecificationParser.detect_category(
        title="Samsung Galaxy S24 Ultra 5G (Titanium Gray, 256 GB) (12 GB RAM)",
        raw_specs={"Internal Storage": "256 GB", "RAM": "12 GB"}
    )
    assert cat == "MOBILE"

    # Fashion
    cat = SpecificationParser.detect_category(
        title="Men Slim Fit Cotton Casual Shirt",
        raw_specs={"Fabric": "100% Cotton", "Pattern": "Solid"}
    )
    assert cat == "FASHION"

    # Home
    cat = SpecificationParser.detect_category(
        title="Double Bed Bedsheet 100% Cotton with Pillow Covers",
        raw_specs={"Material": "Glaze Cotton", "Thread Count": "200"}
    )
    assert cat == "HOME"


def test_specification_parser_extraction():
    raw_specs = {
        "RAM": "8 GB",
        "Internal Storage": "128 GB",
        "Primary Camera": "50MP + 8MP",
        "Battery Capacity": "5000 mAh",
        "Processor Type": "Snapdragon 695",
        "Operating System": "Android 14"
    }
    extracted = SpecificationParser.structure_specifications("MOBILE", raw_specs)
    cat_specs = extracted.get("category_specific", {})
    assert cat_specs.get("RAM") == "8 GB"
    assert cat_specs.get("ROM") == "128 GB"
    assert cat_specs.get("Battery") == "5000 mAh"


def test_data_normalizer_price():
    assert DataNormalizer.parse_price("₹1,299") == 1299.0
    assert DataNormalizer.parse_price("Rs. 45,999.00") == 45999.0
    assert DataNormalizer.parse_price(999) == 999.0
    assert DataNormalizer.parse_price("Free") is None


def test_data_validator_completeness():
    prod = ProductInfo(
        product_name="Sample Smartphone Pro",
        brand="TechBrand",
        current_price=19999.0,
        original_price=24999.0,
        discount="20% off",
        rating=4.3,
        total_reviews_count=150,
        product_url="https://www.flipkart.com/sample/p/123",
        platform="flipkart",
        specifications={"RAM": "8 GB"}
    )
    status = DataValidator.evaluate_product_completeness(prod)
    assert status["product_name"] == "FOUND"
    assert status["current_price"] == "FOUND"
    assert status["brand"] == "FOUND"
    assert status["rating"] == "FOUND"
    assert status["specifications"] == "FOUND"


def test_data_validator_deduplication():
    reviews = [
        CustomerReview(review_id="r1", review_text="Great quality product!", platform="flipkart"),
        CustomerReview(review_id="r1", review_text="Great quality product!", platform="flipkart"),
        CustomerReview(review_id="r2", review_text="Loved the fast delivery and build.", platform="flipkart"),
        CustomerReview(review_id="r3", review_text="Great quality product!", platform="flipkart"),  # duplicate text
    ]
    unique, dups = DataValidator.deduplicate_reviews(reviews)
    assert len(unique) == 2
    assert dups == 2


def test_pagination_manager():
    pm = PaginationManager(max_reviews=15)
    assert pm.should_continue() is True
    pm.record_page_results(10)
    assert pm.should_continue() is True
    pm.record_page_results(5)
    # Total reached 15 == max_reviews
    assert pm.should_continue() is False
    # If 0 items returned on page or has_more is False
    pm2 = PaginationManager(max_reviews=50)
    pm2.record_page_results(0, has_more=False)
    assert pm2.should_continue() is False


def test_platform_url_parsers():
    # Amazon ASIN
    assert AmazonScraper.extract_asin("https://www.amazon.in/dp/B0CX24T4NQ") == "B0CX24T4NQ"
    assert AmazonScraper.extract_asin("https://www.amazon.in/gp/product/B07HGH88XX/ref=...") == "B07HGH88XX"

    # Flipkart PID
    f_info = FlipkartScraper.extract_ids("https://www.flipkart.com/motorola-g34-5g-charcoal-black-128-gb/p/itm4b76?pid=MOBGUFK4PZX")
    assert f_info["item_id"] == "itm4b76"
    assert f_info["pid"] == "MOBGUFK4PZX"

    # Meesho Product Code
    assert MeeshoScraper.extract_product_code("https://www.meesho.com/s/p/7t0x6p") == "7t0x6p"

    # AJIO Product Code
    assert AjioScraper.extract_product_code("https://www.ajio.com/gap-men-solid-crew-neck-t-shirt/p/460492837_blue") == "460492837_blue"

    # Myntra Style ID
    assert MyntraScraper.extract_style_id("https://www.myntra.com/tshirts/roadster/roadster-men-black-cotton-pure-cotton-t-shirt/2127874/buy") == "2127874"


def test_amazon_review_parsing_and_cleaning():
    from bs4 import BeautifulSoup
    sample_html = """
    <div data-hook="review" id="R123456789">
        <span class="a-profile-name">Priya Sharma</span>
        <a data-hook="review-title"><span>Excellent camera and battery life!</span></a>
        <i data-hook="review-star-rating"><span class="a-icon-alt">4.5 out of 5 stars</span></i>
        <span data-hook="review-date">Reviewed in India on 15 August 2024</span>
        <span data-hook="avp-badge">Verified Purchase</span>
        <span data-hook="helpful-vote-statement">24 people found this helpful</span>
        <a data-hook="format-strip">Colour: Titanium Gray | Size: 256 GB</a>
        <span data-hook="review-body">
            <span>The build quality is superb. Display is bright outdoors and battery easily lasts 1.5 days. Read more</span>
        </span>
    </div>
    """
    soup = BeautifulSoup(sample_html, "lxml")
    reviews = AmazonScraper._parse_reviews_from_soup(soup)
    assert len(reviews) == 1
    r = reviews[0]
    assert r.review_id.startswith("amazon_")
    assert r.reviewer_name == "Priya Sharma"
    assert r.review_title == "Excellent camera and battery life!"
    assert r.rating == 4.5
    assert r.verified_purchase is True
    assert r.helpful_votes == 24
    assert "Titanium Gray" in (r.product_variant or "")
    assert r.review_text.endswith("lasts 1.5 days.")  # "Read more" stripped
    assert not r.review_text.endswith("Read more")


def test_flipkart_review_parsing_and_helpful_votes():
    from bs4 import BeautifulSoup
    sample_html = """
    <div class="EPCmJX">
        <div class="row">
            <div class="XQDdHH">5<img src="star.svg"/></div>
            <p class="z9E0IG">Terrific purchase</p>
        </div>
        <div class="row">
            <div class="ZmyHeo">
                <div><div>Great performance for gaming and everyday multitasking. Display 120Hz is buttery smooth. READ MORE</div></div>
            </div>
        </div>
        <div class="row">
            <div class="_2V5EHH"><span>Charcoal Black, 128 GB</span></div>
        </div>
        <div class="row">
            <p class="_2sc7ZR _2V5EHH">Rahul Verma</p>
            <p class="_2mcFHG">Certified Buyer</p>
            <p class="_2sc7ZR">2 months ago</p>
            <div class="_1LmwT9"><span>142</span></div>
        </div>
    </div>
    """
    soup = BeautifulSoup(sample_html, "lxml")
    reviews = FlipkartScraper._parse_reviews_from_soup(soup)
    assert len(reviews) == 1
    r = reviews[0]
    assert r.review_id.startswith("flipkart_")
    assert r.reviewer_name == "Rahul Verma"
    assert r.review_title == "Terrific purchase"
    assert r.rating == 5.0
    assert r.verified_purchase is True
    assert r.helpful_votes == 142
    assert "Charcoal Black" in (r.product_variant or "")
    assert r.review_text.endswith("buttery smooth.")  # "READ MORE" stripped
    assert r.review_date == "2 months ago"


def test_meesho_embedded_review_parsing():
    import json
    from bs4 import BeautifulSoup
    ssr_data = {
        "props": {
            "pageProps": {
                "initialState": {
                    "product": {
                        "details": {
                            "name": "Women Floral Print Rayon Anarkali Kurta",
                            "price": 499,
                            "rating": 4.3,
                            "review_count": 850
                        }
                    }
                },
                "reviews": {
                    "data": [
                        {
                            "id": "m_rev_101",
                            "author": "Anjali K",
                            "rating": 5,
                            "comment": "Fabric is soft and comfortable. Perfect fit for daily wear. ...more",
                            "created_at": "2024-09-10",
                            "verified_purchase": True
                        }
                    ]
                }
            }
        }
    }
    html = f'<html><head><script id="__NEXT_DATA__" type="application/json">{json.dumps(ssr_data)}</script></head><body></body></html>'
    soup = BeautifulSoup(html, "lxml")
    import asyncio
    reviews, stats = asyncio.run(MeeshoScraper._extract_meesho_reviews(soup, "7t0x6p", max_reviews=10))
    assert len(reviews) == 1
    r = reviews[0]
    assert r.review_id.startswith("meesho_")
    assert r.reviewer_name == "Anjali K"
    assert r.rating == 5.0
    assert r.verified_purchase is True
    assert r.review_text.endswith("daily wear.")  # "...more" stripped
    assert stats["stop_reason"] == "embedded_page_reviews"


def test_myntra_review_parsing():
    from bs4 import BeautifulSoup
    from unittest.mock import patch
    sample_html = """
    <div class="user-review-main">
        <div class="user-review-left">
            <span class="user-review-userName">Vikram Singh</span>
            <div class="user-review-reviewDate">12 Oct 2024</div>
        </div>
        <div class="user-review-starRating"><span>4</span></div>
        <div class="user-review-reviewTextWrapper">
            Pure cotton fabric feels premium. Stitching is solid. See more
        </div>
        <div class="user-review-verifiedBuyer">Verified Buyer</div>
        <span class="user-review-userSize">Size: L</span>
        <span class="user-review-upvoteCount">38</span>
    </div>
    """
    soup = BeautifulSoup(sample_html, "lxml")
    import asyncio
    async def mock_collect(url, platform, initial_reviews=None, max_reviews=None, progress_callback=None, review_page_url=None):
        return list(initial_reviews or []), {"stop_reason": "soup_parsed", "retrieved_reviews": len(initial_reviews or [])}

    with patch("backend.ecommerce.myntra_scraper.collect_public_reviews", side_effect=mock_collect):
        reviews, stats = asyncio.run(MyntraScraper._extract_myntra_reviews(soup, "https://www.myntra.com/sample/buy", style_id=None, max_reviews=10))
    assert len(reviews) == 1
    r = reviews[0]
    assert r.review_id.startswith("myntra_")
    assert r.reviewer_name == "Vikram Singh"
    assert r.rating == 4.0
    assert r.verified_purchase is True
    assert r.helpful_votes == 38
    assert "Size: L" in (r.product_variant or "")
    assert r.review_text.endswith("Stitching is solid.")  # "See more" stripped

