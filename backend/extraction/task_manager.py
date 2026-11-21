import time
import asyncio
from typing import Dict, Any, Optional, List
from backend.extraction.models import (
    EngineType,
    EngineStatus,
    OverallStatus,
    DataStatus,
    ExtractionStats,
    ExtractionEvent,
    EngineExecutionState
)
from backend.schemas.api_schemas import NormalizedComment


class ExtractionTaskState:
    """Represents the complete live state of an extraction task."""

    def __init__(self, task_id: str, url: str, platform: str = "general", max_records: int = 100):
        self.task_id = task_id
        self.url = url
        self.platform = platform
        self.max_records = max_records
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = OverallStatus.RUNNING
        self.progress: float = 5.0
        self.active_stage: str = "Initializing universal extraction pipeline..."
        self.cancel_requested: bool = False

        # Live stats
        self.stats = ExtractionStats()

        # Engine states for the 4 core engines
        self.engines: Dict[str, EngineExecutionState] = {
            EngineType.CRAWL4AI.value: EngineExecutionState(
                engine=EngineType.CRAWL4AI, display_name="Crawl4AI Engine", status=EngineStatus.WAITING
            ),
            EngineType.PLAYWRIGHT.value: EngineExecutionState(
                engine=EngineType.PLAYWRIGHT, display_name="Playwright Headless", status=EngineStatus.WAITING
            ),
            EngineType.SCRAPY.value: EngineExecutionState(
                engine=EngineType.SCRAPY, display_name="Scrapy Spider", status=EngineStatus.WAITING
            ),
            EngineType.BEAUTIFUL_SOUP.value: EngineExecutionState(
                engine=EngineType.BEAUTIFUL_SOUP, display_name="BeautifulSoup 4", status=EngineStatus.WAITING
            ),
        }

        # Activity log entries
        self.logs: List[Dict[str, Any]] = []
        self.event_sequence = 0
        self.event_queue: asyncio.Queue = asyncio.Queue()

        # Final collected items & analysis
        self.final_comments: List[NormalizedComment] = []
        self.metadata: Dict[str, Any] = {}
        self.analysis_result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None

    def add_log(self, message: str, level: str = "info", engine: Optional[str] = None):
        t_str = time.strftime("%H:%M:%S")
        entry = {
            "timestamp": t_str,
            "message": message,
            "level": level,
            "engine": engine
        }
        self.logs.append(entry)
        self.push_event("log", entry)

    def update_engine(
        self,
        engine: str,
        status: EngineStatus,
        last_op: str,
        records: int = 0,
        exec_time: float = 0.0,
        failure_reason: Optional[str] = None,
        data_status: DataStatus = DataStatus.PAGE_LOADED
    ):
        if engine in self.engines:
            st = self.engines[engine]
            st.status = status
            st.last_operation = last_op
            st.records_extracted = records
            st.execution_time_sec = round(exec_time, 2)
            st.failure_reason = failure_reason
            st.data_status = data_status

            self.push_event("engine_status", {
                "engine": engine,
                "status": status.value,
                "last_operation": last_op,
                "records_extracted": records,
                "execution_time_sec": round(exec_time, 2),
                "failure_reason": failure_reason,
                "data_status": data_status.value
            })

    def update_progress(self, progress: float, stage: str):
        self.progress = round(progress, 1)
        self.active_stage = stage
        self.push_event("progress", {
            "progress": self.progress,
            "stage": stage
        })

    def push_event(self, event_type: str, data: Dict[str, Any]):
        self.event_sequence += 1
        t_str = time.strftime("%H:%M:%S")
        event = ExtractionEvent(
            task_id=self.task_id,
            sequence=self.event_sequence,
            timestamp=t_str,
            event_type=event_type,
            data=data
        )
        try:
            self.event_queue.put_nowait(event)
        except Exception:
            pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "url": self.url,
            "platform": self.platform,
            "status": self.status.value,
            "progress": self.progress,
            "active_stage": self.active_stage,
            "elapsed_sec": round(time.time() - self.start_time, 2) if not self.end_time else round(self.end_time - self.start_time, 2),
            "stats": self.stats.model_dump(),
            "engines": {k: v.model_dump() for k, v in self.engines.items()},
            "logs": self.logs[-40:],
            "metadata": self.metadata,
            "comments_count": len(self.final_comments),
            "has_analysis": self.analysis_result is not None,
            "error": self.error_message
        }


class ExtractionTaskManager:
    """Thread-safe registry for extraction tasks."""
    _tasks: Dict[str, ExtractionTaskState] = {}

    @classmethod
    def create_task(cls, task_id: str, url: str, platform: str, max_records: int) -> ExtractionTaskState:
        state = ExtractionTaskState(task_id=task_id, url=url, platform=platform, max_records=max_records)
        cls._tasks[task_id] = state
        return state

    @classmethod
    def get_task(cls, task_id: str) -> Optional[ExtractionTaskState]:
        return cls._tasks.get(task_id)

    @classmethod
    def cancel_task(cls, task_id: str) -> bool:
        task = cls._tasks.get(task_id)
        if task and task.status == OverallStatus.RUNNING:
            task.cancel_requested = True
            task.status = OverallStatus.CANCELLED
            task.end_time = time.time()
            task.update_progress(task.progress, "Cancellation requested")
            task.add_log("Cancellation requested by user", level="warning")
            return True
        return False
