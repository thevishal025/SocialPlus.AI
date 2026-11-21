import time
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ProductInfo(BaseModel):
    """Deep product intelligence data model."""
    product_name: str
    brand: Optional[str] = None
    product_images: List[str] = Field(default_factory=list)
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    discount: Optional[str] = None
    discount_percent: Optional[float] = None
    currency: str = "INR"
    description: Optional[str] = None
    category: str = "GENERAL"  # MOBILE, FASHION, HOME, ELECTRONICS, GENERAL
    specifications: Dict[str, Any] = Field(default_factory=dict)
    category_specific_specs: Dict[str, Any] = Field(default_factory=dict)
    variants: List[str] = Field(default_factory=list)
    color: Optional[str] = None
    size: Optional[str] = None
    availability: Optional[str] = "In Stock"
    rating: Optional[float] = None
    total_reviews_count: Optional[int] = None
    review_count: Optional[int] = None
    product_url: str
    platform: str
    extraction_timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    completeness: Dict[str, str] = Field(default_factory=dict)
    description_data: Dict[str, Any] = Field(default_factory=dict)
    technical_specifications: Dict[str, Any] = Field(default_factory=dict)
    variants_data: Dict[str, List[str]] = Field(default_factory=dict)
    extraction_info: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.review_count is None and self.total_reviews_count is not None:
            self.review_count = self.total_reviews_count
        elif self.total_reviews_count is None and self.review_count is not None:
            self.total_reviews_count = self.review_count

        if not self.category_specific_specs and self.specifications:
            cat_s = self.specifications.get("category_specific") or self.specifications.get("category_specific_specs")
            if not cat_s:
                for k in ["mobile_specifications", "fashion_specifications", "home_specifications"]:
                    if k in self.specifications:
                        cat_s = self.specifications[k]
                        break
            if cat_s and isinstance(cat_s, dict):
                self.category_specific_specs = cat_s

        if not self.technical_specifications:
            self.technical_specifications = dict(self.category_specific_specs) if self.category_specific_specs else dict(self.specifications.get("raw", {}))

        if not self.description_data:
            self.description_data = {
                "description": self.description or "Not available",
                "features": [],
                "highlights": [],
                "manufacturer": "Not available"
            }

        if not self.variants_data:
            self.variants_data = {
                "sizes": [self.size] if self.size else [],
                "colors": [self.color] if self.color else [],
                "models": [],
                "storage": [],
                "options": list(self.variants) if self.variants else []
            }

        if not self.extraction_info:
            self.extraction_info = {
                "platform": self.platform,
                "source_url": self.product_url,
                "extraction_timestamp": self.extraction_timestamp,
                "reported_reviews": self.total_reviews_count,
                "extracted_reviews": 0,
                "unique_reviews": 0,
                "status": "extracted"
            }

        if self.discount_percent is None:
            if self.current_price and self.original_price and self.original_price > self.current_price:
                self.discount_percent = round((1 - self.current_price / self.original_price) * 100, 1)
            elif self.discount:
                m = re.search(r"(\d+(\.\d+)?)%", str(self.discount))
                if m:
                    try:
                        self.discount_percent = float(m.group(1))
                    except Exception:
                        pass


class SpecificationParser:
    """
    Category-specific dynamic specification extractor.
    Understands distinctions between Mobile (RAM/ROM/Battery/Camera),
    Fashion (Fabric/Material/Fit/Care), and Home (Dimensions/Material/Weight).
    """

    @classmethod
    def detect_category(cls, title: str, raw_specs: Dict[str, Any]) -> str:
        text = (title + " " + " ".join([f"{k} {v}" for k, v in raw_specs.items()])).lower()

        mobile_kws = ["smartphone", "phone", "mobile", "iphone", "ipad", "tablet", "ram", "rom", "snapdragon", "camera", "battery", "mah", "amoled", "5g", "android", "ios", "storage"]
        fashion_kws = ["shirt", "t-shirt", "dress", "kurti", "saree", "jeans", "fabric", "cotton", "polyester", "wear", "fit", "sleeve", "trouser", "shoes"]
        home_kws = ["furniture", "chair", "table", "bed", "bedsheet", "sheet", "pillow", "mattress", "kitchen", "cookware", "curtain", "cushion", "dimensions", "decor", "sofa"]

        m_score = sum(1 for kw in mobile_kws if kw in text)
        f_score = sum(1 for kw in fashion_kws if kw in text)
        h_score = sum(1 for kw in home_kws if kw in text)

        if m_score >= 2 and m_score >= f_score and m_score >= h_score:
            return "MOBILE"
        elif f_score >= 2 and f_score >= m_score and f_score >= h_score:
            return "FASHION"
        elif h_score >= 2 and h_score >= m_score and h_score >= f_score:
            return "HOME"
        return "GENERAL"

    @classmethod
    def structure_specifications(cls, category: str, raw_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Maps unstructured raw specifications into category-tailored schemas."""
        structured = {"raw": raw_specs}

        if category == "MOBILE":
            mobile_mapping = {
                "RAM": ["ram", "memory"],
                "ROM": ["internal storage", "rom", "storage"],
                "Processor": ["processor", "chipset", "cpu", "processor core"],
                "Display": ["display size", "resolution", "display type", "screen"],
                "Camera": ["primary camera", "rear camera", "front camera", "camera"],
                "Battery": ["battery capacity", "battery", "mah"],
                "Operating System": ["operating system", "os"],
                "Connectivity": ["network type", "supported networks", "connectivity"],
                "Charging": ["fast charge", "charging", "charger"],
                "Warranty": ["warranty summary", "warranty"]
            }
            category_specs = {}
            for target_field, aliases in mobile_mapping.items():
                for k, v in raw_specs.items():
                    if any(alias in k.lower() for alias in aliases):
                        category_specs[target_field] = str(v).strip()
                        break
            structured["mobile_specifications"] = category_specs
            structured["category_specific"] = category_specs

        elif category == "FASHION":
            fashion_mapping = {
                "Fabric": ["fabric", "fabric care", "material"],
                "Cotton Type": ["cotton type", "cotton blend"],
                "Fit": ["fit", "fit/shape"],
                "Pattern": ["pattern", "design"],
                "Color": ["color", "shade"],
                "Care Instructions": ["care instructions", "wash care", "fabric care"],
                "Neck/Collar": ["neck", "collar"],
                "Sleeve": ["sleeve length", "sleeve"]
            }
            category_specs = {}
            for target_field, aliases in fashion_mapping.items():
                for k, v in raw_specs.items():
                    if any(alias in k.lower() for alias in aliases):
                        category_specs[target_field] = str(v).strip()
                        break
            structured["fashion_specifications"] = category_specs
            structured["category_specific"] = category_specs
            structured["category_specific_specs"] = category_specs

        elif category == "HOME":
            home_mapping = {
                "Material": ["material", "primary material"],
                "Dimensions": ["dimensions", "width", "height", "depth"],
                "Weight": ["weight", "item weight"],
                "Capacity": ["capacity", "volume"],
                "Features": ["features", "suitable for"]
            }
            category_specs = {}
            for target_field, aliases in home_mapping.items():
                for k, v in raw_specs.items():
                    if any(alias in k.lower() for alias in aliases):
                        category_specs[target_field] = str(v).strip()
                        break
            structured["home_specifications"] = category_specs
            structured["category_specific"] = category_specs
            structured["category_specific_specs"] = category_specs
        else:
            # GENERAL: Pick first 6 clean key-value pairs
            gen_specs = {k: str(v).strip() for k, v in list(raw_specs.items())[:6] if str(v).strip()}
            structured["category_specific"] = gen_specs
            structured["category_specific_specs"] = gen_specs

        return structured
