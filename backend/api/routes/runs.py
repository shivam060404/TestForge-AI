from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import asyncio
import json

from core.database import get_db
from models.project import Project
from models.test_case import TestCase
from models.environment import Environment
from models.run import TestRun, StepExecution, RunStatus, StepStatus
from models.healing import HealingCandidate, HealingStatus
from schemas import (
    TestRunCreate, TestRunResponse, TestRunDetailResponse, StepExecutionResponse,
    PaginationParams, PaginatedResponse,
)
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# In-memory event subscribers for SSE
_event_subscribers: dict[UUID, list[asyncio.Queue]] = {}


async def _broadcast_event(run_id: UUID, event_type: str, data: dict):
    """Broadcast event to all subscribers of a run."""
    if run_id in _event_subscribers:
        event = {
            "type": event_type,
            "run_id": str(run_id),
            "timestamp": data.get("timestamp"),
            "data": data,
        }
        for queue in _event_subscribers[run_id]:
            await queue.put(event)


@router.get("/projects/{project_id}/runs", response_model=PaginatedResponse)
async def list_runs(
    project_id: UUID,
    pagination: PaginationParams = Depends(),
    status: Optional[RunStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    stmt = select(TestRun).where(TestRun.project_id == project_id).order_by(TestRun.created_at.desc())
    if status:
        stmt = stmt.where(TestRun.status == status)
    
    count_stmt = select(func.count()).select_from(TestRun).where(TestRun.project_id == project_id)
    if status:
        count_stmt = count_stmt.where(TestRun.status == status)
    
    total = await db.scalar(count_stmt)
    result = await db.execute(
        stmt.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    )
    runs = result.scalars().all()
    
    return PaginatedResponse(
        items=[TestRunResponse.model_validate(r) for r in runs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.post("/projects/{project_id}/runs", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    project_id: UUID,
    run_in: TestRunCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    test_case = await db.get(TestCase, run_in.test_case_id)
    if not test_case or test_case.project_id != project_id:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    env = await db.get(Environment, run_in.environment_id)
    if not env or env.project_id != project_id:
        raise HTTPException(status_code=404, detail="Environment not found")
    
    run = TestRun(
        project_id=project_id,
        test_case_id=run_in.test_case_id,
        environment_id=run_in.environment_id,
        triggered_by=run_in.triggered_by,
        commit_sha=run_in.commit_sha,
        branch=run_in.branch,
        total_steps=len(test_case.steps),
        status=RunStatus.PENDING,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    
    # Create step executions
    for i, step_data in enumerate(test_case.steps):
        raw_id = step_data.get("id") if isinstance(step_data, dict) else getattr(step_data, "id", None)
        try:
            step_uuid = UUID(str(raw_id)) if raw_id else uuid.uuid4()
        except (ValueError, AttributeError):
            step_uuid = uuid.uuid4()
        step_exec = StepExecution(
            run_id=run.id,
            step_id=step_uuid,
            order=i,
            status=StepStatus.PENDING,
        )
        db.add(step_exec)
    
    await db.commit()
    await db.refresh(run)
    
    logger.info("run_created", run_id=str(run.id), project_id=str(project_id))
    
    # TODO: Queue run for execution by worker
    # await queue_run_for_execution(run.id)
    
    return TestRunResponse.model_validate(run)


@router.get("/runs/{run_id}", response_model=TestRunDetailResponse)
async def get_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(TestRun)
        .options(selectinload(TestRun.step_executions))
        .where(TestRun.id == run_id)
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run_detail = TestRunDetailResponse.model_validate(run)
    run_detail.step_executions = [StepExecutionResponse.model_validate(se) for se in run.step_executions]
    return run_detail


@router.get("/runs/{run_id}/events")
async def stream_run_events(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    queue: asyncio.Queue = asyncio.Queue()
    
    if run_id not in _event_subscribers:
        _event_subscribers[run_id] = []
    _event_subscribers[run_id].append(queue)
    
    async def event_generator():
        try:
            # Send initial state
            yield f"data: {json.dumps({'type': 'connected', 'run_id': str(run_id)})}\n\n"
            
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
                
                # Stop streaming if run is complete
                if event["type"] in ("run_completed", "run_cancelled"):
                    break
        finally:
            _event_subscribers[run_id].remove(queue)
            if not _event_subscribers[run_id]:
                del _event_subscribers[run_id]
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/runs/{run_id}/cancel", response_model=TestRunResponse)
async def cancel_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.status not in (RunStatus.PENDING, RunStatus.RUNNING, RunStatus.HEALING):
        raise HTTPException(status_code=400, detail="Run cannot be cancelled")
    
    run.status = RunStatus.CANCELLED
    await db.commit()
    await db.refresh(run)
    
    await _broadcast_event(run_id, "run_cancelled", {"run_id": str(run_id)})
    logger.info("run_cancelled", run_id=str(run_id))
    
    return TestRunResponse.model_validate(run)


@router.post("/runs/{run_id}/retry", response_model=TestRunResponse)
async def retry_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.status not in (RunStatus.FAILED, RunStatus.CANCELLED):
        raise HTTPException(status_code=400, detail="Only failed or cancelled runs can be retried")
    
    # Create new run with same parameters
    new_run = TestRun(
        project_id=run.project_id,
        test_case_id=run.test_case_id,
        environment_id=run.environment_id,
        triggered_by=run.triggered_by,
        commit_sha=run.commit_sha,
        branch=run.branch,
        total_steps=run.total_steps,
        status=RunStatus.PENDING,
    )
    db.add(new_run)
    await db.commit()
    await db.refresh(new_run)
    
    # Create step executions
    test_case = await db.get(TestCase, run.test_case_id)
    for i, step_data in enumerate(test_case.steps):
        raw_id = step_data.get("id") if isinstance(step_data, dict) else getattr(step_data, "id", None)
        try:
            step_uuid = UUID(str(raw_id)) if raw_id else uuid4()
        except (ValueError, AttributeError):
            step_uuid = uuid4()
        step_exec = StepExecution(
            run_id=new_run.id,
            step_id=step_uuid,
            order=i,
            status=StepStatus.PENDING,
        )
        db.add(step_exec)
    
    await db.commit()
    await db.refresh(new_run)
    
    logger.info("run_retried", original_run_id=str(run_id), new_run_id=str(new_run.id))
    
    # TODO: Queue new run for execution
    
    return TestRunResponse.model_validate(new_run)