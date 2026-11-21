# Forward legacy ecommerce_routes to the dedicated backend.ecommerce module
from backend.ecommerce.ecommerce_router import router
__all__ = ["router"]
