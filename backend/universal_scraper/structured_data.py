import json
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup


class StructuredDataExtractor:
    """
    Universal Scraper Structured Data Extraction Engine.
    Extracts semantic structured metadata across:
    - JSON-LD (<script type="application/ld+json">)
    - OpenGraph (<meta property="og:*">)
    - Twitter Cards (<meta name="twitter:*">)
    - Schema.org Microdata (<... itemscope itemtype="...">)
    - Client-side Hydration States (__NEXT_DATA__, __INITIAL_STATE__, _sharedData)
    """

    @classmethod
    def extract_json_ld(cls, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parses all JSON-LD script blocks into clean python dictionaries."""
        results: List[Dict[str, Any]] = []
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            raw_text = script.string.strip()
            if not raw_text:
                continue
            try:
                data = json.loads(raw_text)
                if isinstance(data, list):
                    results.extend([item for item in data if isinstance(item, dict)])
                elif isinstance(data, dict):
                    if "@graph" in data and isinstance(data["@graph"], list):
                        results.extend([item for item in data["@graph"] if isinstance(item, dict)])
                    else:
                        results.append(data)
            except Exception:
                # Some sites embed multiple JSON objects concatenated
                cleaned = re.sub(r"[\r\n\t]+", " ", raw_text)
                matches = re.findall(r"\{.*?\}", cleaned)
                for m in matches:
                    try:
                        d = json.loads(m)
                        if isinstance(d, dict) and "@context" in d:
                            results.append(d)
                    except Exception:
                        pass
        return results

    @classmethod
    def extract_opengraph_and_meta(cls, soup: BeautifulSoup) -> Dict[str, str]:
        """Extracts standard OpenGraph, Twitter, and canonical meta attributes."""
        meta: Dict[str, str] = {}
        for tag in soup.find_all("meta"):
            prop = tag.get("property") or tag.get("name") or tag.get("itemprop")
            val = tag.get("content") or tag.get("value")
            if prop and val:
                prop_clean = prop.strip().lower()
                val_clean = val.strip()
                if prop_clean not in meta:
                    meta[prop_clean] = val_clean

        # Extract title and canonical tag
        if "title" not in meta and soup.title and soup.title.string:
            meta["title"] = soup.title.string.strip()

        link_canon = soup.find("link", rel="canonical")
        if link_canon and link_canon.get("href"):
            meta["canonical_url"] = link_canon["href"].strip()

        return meta

    @classmethod
    def extract_embedded_state(cls, html_text: str) -> Dict[str, Any]:
        """Extracts framework hydration states (Next.js, Redux, Nuxt, Instagram/Facebook)."""
        state: Dict[str, Any] = {}

        # 1. Next.js __NEXT_DATA__
        m_next = re.search(r'<script\s+id="__NEXT_DATA__"\s+type="application/json">([^<]+)</script>', html_text)
        if m_next:
            try:
                state["next_data"] = json.loads(m_next.group(1))
            except Exception:
                pass

        # 2. Window / React __INITIAL_STATE__
        m_initial = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});\s*</script>', html_text, re.DOTALL)
        if m_initial:
            try:
                state["initial_state"] = json.loads(m_initial.group(1))
            except Exception:
                pass

        # 3. Instagram _sharedData / __additionalData
        m_insta_shared = re.search(r'window\._sharedData\s*=\s*(\{.*?\});\s*</script>', html_text, re.DOTALL)
        if m_insta_shared:
            try:
                state["instagram_shared_data"] = json.loads(m_insta_shared.group(1))
            except Exception:
                pass

        return state

