from typing import Optional
from backend.connectors.base_connector import BaseConnector
from backend.connectors.youtube_connector import YouTubeApiConnector, YouTubePublicConnector
from backend.connectors.instagram_connector import InstagramApiConnector, InstagramPublicConnector
from backend.connectors.facebook_connector import FacebookApiConnector, FacebookPublicConnector
from backend.connectors.ecommerce_connector import EcommerceConnector


class ConnectorRegistry:
    """Central registry resolving platform and method connectors."""

    @staticmethod
    def get_connector(platform: str, method: str, **kwargs) -> Optional[BaseConnector]:
        plat = platform.lower()
        meth = method.lower()

        if plat == "youtube":
            if meth == "api":
                return YouTubeApiConnector(api_key=kwargs.get("api_key"))
            elif meth == "public":
                return YouTubePublicConnector()
        elif plat == "instagram":
            if meth == "api":
                return InstagramApiConnector(access_token=kwargs.get("access_token"))
            elif meth == "public":
                return InstagramPublicConnector()
        elif plat == "facebook":
            if meth == "api":
                return FacebookApiConnector(access_token=kwargs.get("access_token"))
            elif meth == "public":
                return FacebookPublicConnector()
        elif plat == "ecommerce":
            return EcommerceConnector()

        return None

