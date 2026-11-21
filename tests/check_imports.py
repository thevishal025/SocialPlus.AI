import sys
sys.path.insert(0, '.')
from backend.connectors.youtube_connector import YouTubeApiConnector, YouTubePublicConnector
from backend.connectors.ecommerce_connector import EcommerceConnector
from backend.api.youtube_routes import router
from backend.api.ecommerce_routes import router as er
ec = EcommerceConnector()
result = ec.detect_platform_from_url("https://www.flipkart.com/some-product/p/itm123")
print(f"Platform detection: {result}")
print("All imports OK")

