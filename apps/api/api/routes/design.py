from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.project import Project
from models.run import TestRun
from models.design import VisualBaseline, VisualComparison, AccessibilityIssue
from schemas import (
    VisualBaselineResponse, VisualComparisonResponse, AccessibilityIssueResponse, DesignInsightResponse,
)
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/projects/{project_id}/visual-baselines", response_model=List[VisualBaselineResponse])
async def list_visual_baselines(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    stmt = select(VisualBaseline).where(VisualBaseline.project_id == project_id).order_by(VisualBaseline.created_at.desc())
    result = await db.execute(stmt)
    baselines = result.scalars().all()
    
    return [VisualBaselineResponse.model_validate(b) for b in baselines]


@router.post("/projects/{project_id}/visual-baselines", response_model=VisualBaselineResponse, status_code=status.HTTP_201_CREATED)
async def create_visual_baseline(
    project_id: UUID,
    name: str,
    viewport_width: int,
    viewport_height: int,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # TODO: Save image to MinIO/storage
    # For now, use a placeholder path
    image_path = f"baselines/{project_id}/{name}.png"
    
    baseline = VisualBaseline(
        project_id=project_id,
        name=name,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        image_path=image_path,
    )
    db.add(baseline)
    await db.commit()
    await db.refresh(baseline)
    
    logger.info("visual_baseline_created", baseline_id=str(baseline.id), project_id=str(project_id))
    return VisualBaselineResponse.model_validate(baseline)


@router.get("/runs/{run_id}/design-insights", response_model=DesignInsightResponse)
async def get_design_insights(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get visual comparisons
    vc_stmt = select(VisualComparison).where(VisualComparison.run_id == run_id)
    vc_result = await db.execute(vc_stmt)
    visual_comparisons = vc_result.scalars().all()
    
    # Get accessibility issues
    ai_stmt = select(AccessibilityIssue).where(AccessibilityIssue.run_id == run_id)
    ai_result = await db.execute(ai_stmt)
    accessibility_issues = ai_result.scalars().all()
    
    return DesignInsightResponse(
        run_id=run_id,
        visual_comparisons=[VisualComparisonResponse.model_validate(vc) for vc in visual_comparisons],
        accessibility_issues=[AccessibilityIssueResponse.model_validate(ai) for ai in accessibility_issues],
        performance_metrics=None,  # TODO: Implement
    )


@router.get("/visual-baselines/{baseline_id}/compare", response_model=VisualComparisonResponse)
async def compare_visual_baseline(
    baseline_id: UUID,
    run_id: UUID,
    step_execution_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    baseline = await db.get(VisualBaseline, baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Visual baseline not found")
    
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # TODO: Implement actual screenshot comparison
    # For now, return mock result
    comparison = VisualComparison(
        baseline_id=baseline_id,
        run_id=run_id,
        step_execution_id=step_execution_id,
        match=True,
        difference_percent=0.0,
        diff_image_path=None,
        threshold=0.1,
    )
    db.add(comparison)
    await db.commit()
    await db.refresh(comparison)
    
    return VisualComparisonResponse.model_validate(comparison)