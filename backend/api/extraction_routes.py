import uuid
import json
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from backend.extraction.models import StartExtractionRequest, OverallStatus
from backend.extraction.task_manager import ExtractionTaskManager
from backend.extraction.orchestrator import UniversalExtractionOrchestrator
from backend.extraction.performance_history import EnginePerformanceTracker

router = APIRouter(prefix="/api/extraction", tags=["Universal Extraction"])


@router.post("/start")
async def start_extraction(req: StartExtractionRequest):
    """
    Start an extraction task using the Universal Multi-Engine Hybrid Orchestrator.
    Returns immediately with task_id. Live events can be monitored via /events SSE endpoint.
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Target URL cannot be empty.")

    task_id = str(uuid.uuid4())
    platform = UniversalExtractionOrchestrator.detect_platform(url)
    
    # Create task state
    task = ExtractionTaskManager.create_task(
        task_id=task_id,
        url=url,
        platform=platform,
        max_records=req.max_records
    )

    # Launch background task
    asyncio.create_task(UniversalExtractionOrchestrator.run_extraction(task_id))

    return {
        "success": True,
        "task_id": task_id,
        "platform": platform,
        "url": url,
        "status": task.status.value,
        "message": "Universal extraction task started successfully."
    }


@router.get("/{task_id}/status")
def get_task_status(task_id: str):
    """Returns the current snapshot of an extraction task."""
    task = ExtractionTaskManager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    return task.to_dict()


@router.get("/{task_id}/events")
async def stream_task_events(task_id: str):
    """
    Server-Sent Events (SSE) stream for live updates on engines, progress, logs, and statistics.
    """
    task = ExtractionTaskManager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    async def event_generator():
        # First send initial snapshot
        init_data = task.to_dict()
        yield f"event: init\ndata: {json.dumps(init_data)}\n\n"

        # Stream new events as they occur
        while True:
            try:
                # Wait for next event with a timeout for keepalive
                event = await asyncio.wait_for(task.event_queue.get(), timeout=15.0)
                yield f"event: {event.event_type}\ndata: {json.dumps(event.model_dump())}\n\n"

                # If task has completed, failed, or was cancelled, send final event and exit
                if event.event_type in ("completed", "error"):
                    break
            except asyncio.TimeoutError:
                # Send keepalive ping
                if task.status in (OverallStatus.COMPLETED, OverallStatus.FAILED, OverallStatus.CANCELLED):
                    yield f"event: completed\ndata: {json.dumps(task.to_dict())}\n\n"
                    break
                yield f": keepalive\n\n"
            except Exception:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/{task_id}/cancel")
def cancel_task(task_id: str):
    """Cancel a running extraction task."""
    success = ExtractionTaskManager.cancel_task(task_id)
    if not success:
        return {"success": False, "message": "Task already completed, failed, or not found."}
    return {"success": True, "message": "Task cancellation requested."}


@router.post("/{task_id}/retry")
async def retry_task(task_id: str):
    """Retry an extraction task with the same configuration."""
    prev_task = ExtractionTaskManager.get_task(task_id)
    if not prev_task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    new_task_id = str(uuid.uuid4())
    task = ExtractionTaskManager.create_task(
        task_id=new_task_id,
        url=prev_task.url,
        platform=prev_task.platform,
        max_records=prev_task.max_records
    )

    asyncio.create_task(UniversalExtractionOrchestrator.run_extraction(new_task_id))

    return {
        "success": True,
        "task_id": new_task_id,
        "message": f"Task retried with new ID {new_task_id}."
    }


@router.get("/{task_id}/result")
def get_task_result(task_id: str):
    """Returns the final analyzed data result of the extraction task."""
    task = ExtractionTaskManager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

    if task.status != OverallStatus.COMPLETED:
        return {
            "success": False,
            "status": task.status.value,
            "message": task.error_message or "Task has not completed successfully.",
            "task": task.to_dict()
        }

    return {
        "success": True,
        "status": "success",
        "task_id": task_id,
        "platform": task.platform,
        "comments_count": len(task.final_comments),
        "analysis": task.analysis_result,
        "metadata": task.metadata
    }


@router.get("/performance")
def get_performance_stats():
    """Returns historical execution performance data across all extraction engines."""
    return EnginePerformanceTracker.get_summary()

