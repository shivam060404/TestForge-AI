from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.run import TestRun
from models.healing import HealingCandidate, HealingStatus
from schemas import HealingCandidateResponse, ApproveHealingRequest
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
        # TODO: Update step execution with healed locator
        # TODO: Store in locator memory
    else:
        candidate.status = HealingStatus.REJECTED
    
    candidate.reviewed_at = candidate.reviewed_at or candidate.created_at
    candidate.reviewed_by = "user"  # TODO: Get from auth
    
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