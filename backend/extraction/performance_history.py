import json
import os
import time
from typing import Dict, Any, List
from backend.extraction.models import EngineType


PERF_FILE_PATH = os.path.join(os.path.dirname(__file__), "performance_data.json")


class EnginePerformanceTracker:
    """
    Records and tracks execution performance history for each engine across platforms.
    Helps adaptively prioritize engines that have demonstrated higher reliability.
    """

    @classmethod
    def _load_data(cls) -> Dict[str, Any]:
        if not os.path.exists(PERF_FILE_PATH):
            return {
                "crawl4ai": {"success": 0, "failure": 0, "records": 0, "avg_time": 0.0},
                "playwright": {"success": 0, "failure": 0, "records": 0, "avg_time": 0.0},
                "scrapy": {"success": 0, "failure": 0, "records": 0, "avg_time": 0.0},
                "beautifulsoup": {"success": 0, "failure": 0, "records": 0, "avg_time": 0.0},
                "history": []
            }
        try:
            with open(PERF_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"history": []}

    @classmethod
    def _save_data(cls, data: Dict[str, Any]):
        try:
            with open(PERF_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @classmethod
    def record_execution(
        cls,
        engine: EngineType,
        platform: str,
        execution_time: float,
        success: bool,
        records_count: int,
        error_category: str = ""
    ):
        data = cls._load_data()
        key = engine.value
        if key not in data:
            data[key] = {"success": 0, "failure": 0, "records": 0, "avg_time": 0.0}

        entry = data[key]
        if success:
            entry["success"] += 1
            entry["records"] += records_count
        else:
            entry["failure"] += 1

        total = entry["success"] + entry["failure"]
        prev_avg = entry.get("avg_time", 0.0)
        entry["avg_time"] = round((prev_avg * (total - 1) + execution_time) / total, 2)

        # Append to log
        if "history" not in data:
            data["history"] = []
        data["history"].append({
            "timestamp": time.time(),
            "engine": key,
            "platform": platform,
            "duration": round(execution_time, 2),
            "success": success,
            "records": records_count,
            "error_category": error_category
        })
        # Keep last 50 history entries
        data["history"] = data["history"][-50:]

        cls._save_data(data)

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        return cls._load_data()

