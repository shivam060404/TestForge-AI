from typing import List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.run import TestRun, StepExecution, StepStatus
from models.healing import HealingCandidate, HealingStatus
from models.environment import Environment
from schemas import HealingCandidateResponse, ApproveHealingRequest
from services.memory import memory_service
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/runs/{run_id}/healing-candidates", response_model=List[HealingCandidateResponse])
async def list_healing_candidates(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    stmt = select(HealingCandidate).where(HealingCandidate.run_id == run_id).order_by(HealingCandidate.created_at.desc())
    result = await db.execute(stmt)
    candidates = result.scalars().all()
    
    return [HealingCandidateResponse.model_validate(c) for c in candidates]


@router.post("/healing-candidates/{candidate_id}/approve", response_model=HealingCandidateResponse)
async def approve_healing(
    candidate_id: UUID,
    request: ApproveHealingRequest,
    db: AsyncSession = Depends(get_db),
):
    if request.candidate_id != candidate_id:
        raise HTTPException(status_code=400, detail="Candidate ID mismatch")
    
    candidate = await db.get(HealingCandidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Healing candidate not found")
    
    if candidate.status != HealingStatus.PENDING:
        raise HTTPException(status_code=400, detail="Candidate already reviewed")
    
    if request.approved:
        candidate.status = HealingStatus.APPROVED

        # Persist healed locator onto the step execution
        step_exec = await db.get(StepExecution, candidate.step_execution_id)
        if step_exec:
            step_exec.healed_locator = candidate.suggested_locator
            step_exec.status = StepStatus.HEALED

        # Store in locator memory so future runs use the learned locator
        run = await db.get(TestRun, candidate.run_id)
        if run:
            page_url = ""
            env = await db.get(Environment, run.environment_id)
            if env:
                page_url = env.base_url
            await memory_service.record_locator_success(
                project_id=run.project_id,
                selector=candidate.suggested_locator,
                strategy=candidate.suggested_strategy,
                page_url=page_url,
            )
    else:
        candidate.status = HealingStatus.REJECTED

    candidate.reviewed_at = datetime.now(timezone.utc)
    candidate.reviewed_by = "user"
    
    await db.commit()
    await db.refresh(candidate)
    
    logger.info("healing_reviewed", candidate_id=str(candidate_id), approved=request.approved)
    
    return HealingCandidateResponse.model_validate(candidate)


@router.post("/healing-candidates/{candidate_id}/reject", response_model=HealingCandidateResponse)
async def reject_healing(
    candidate_id: UUID,
    request: ApproveHealingRequest,
    db: AsyncSession = Depends(get_db),
):
    return await approve_healing(candidate_id, ApproveHealingRequest(candidate_id=candidate_id, approved=False), db)