import time
import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.schemas.api_schemas import NormalizedComment


class EngineType(str, Enum):
    CRAWL4AI = "crawl4ai"
    PLAYWRIGHT = "playwright"
    SCRAPY = "scrapy"
    BEAUTIFUL_SOUP = "beautifulsoup"
    API = "api"
    UPLOAD = "upload"


class EngineStatus(str, Enum):
    WAITING = "WAITING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class DataStatus(str, Enum):
    PAGE_LOADED = "PAGE_LOADED"
    METADATA_EXTRACTED = "METADATA_EXTRACTED"
    COMMENTS_FOUND = "COMMENTS_FOUND"
    REVIEWS_FOUND = "REVIEWS_FOUND"
    DATA_VALIDATED = "DATA_VALIDATED"
    PARTIAL_EXTRACTION = "PARTIAL_EXTRACTION"
    EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class OverallStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class EngineExecutionState(BaseModel):
    engine: EngineType
    display_name: str
    status: EngineStatus = EngineStatus.WAITING
    execution_time_sec: float = 0.0
    records_extracted: int = 0
    last_operation: str = "Waiting in queue"
    failure_reason: Optional[str] = None
    data_status: DataStatus = DataStatus.PAGE_LOADED


class ExtractionStats(BaseModel):
    total_records: int = 0
    unique_records: int = 0
    duplicates_removed: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    pages_processed: int = 0
    engines_attempted: int = 0
    engines_successful: int = 0


class ExtractionEvent(BaseModel):
    task_id: str
    sequence: int
    timestamp: str
    event_type: str  # init, platform_detected, engine_status, log, stats, progress, completed, error
    data: Dict[str, Any] = Field(default_factory=dict)


class StartExtractionRequest(BaseModel):
    url: str
    max_records: int = Field(default=200, ge=1, le=5000)
    strategy: Optional[str] = "hybrid"  # hybrid, fast, comprehensive

