import time
import abc
from typing import List, Dict, Any, Tuple, Optional
from backend.schemas.api_schemas import NormalizedComment
from backend.extraction.models import EngineType, EngineStatus, DataStatus, EngineExecutionState


class BaseEngine(abc.ABC):
    """
    Abstract interface for every Universal Extraction Engine.
    All engines must implement extract() and is_available().
    """
    engine_type: EngineType
    display_name: str

    def __init__(self):
        self.state = EngineExecutionState(
            engine=self.engine_type,
            display_name=self.display_name,
            status=EngineStatus.WAITING,
            execution_time_sec=0.0,
            records_extracted=0,
            last_operation="Initialized engine",
            data_status=DataStatus.PAGE_LOADED
        )

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Returns True if the required libraries and environments are present."""
        pass

    @abc.abstractmethod
    async def extract(
        self,
        url: str,
        platform: str,
        max_records: int = 100,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[NormalizedComment], Dict[str, Any], EngineStatus, DataStatus, str]:
        """
        Execute extraction using this engine.
        Returns:
            (comments: List[NormalizedComment],
             metadata: Dict[str, Any],
             status: EngineStatus,
             data_status: DataStatus,
             message_or_error: str)
        """
        pass

