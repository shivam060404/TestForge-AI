from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.project import Project
from models.memory import LocatorMemory, EpisodeMemory, FailurePattern
from models.design import VisualBaseline
from schemas import (
    LocatorMemoryResponse, EpisodeMemoryResponse, FailurePatternResponse,
    VisualBaselineResponse, SearchMemoryRequest, SearchMemoryResponse,
)
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/projects/{project_id}/memory/locators", response_model=List[LocatorMemoryResponse])
async def list_locator_memory(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    stmt = select(LocatorMemory).where(LocatorMemory.project_id == project_id).order_by(LocatorMemory.last_used_at.desc())
    result = await db.execute(stmt)
    memories = result.scalars().all()
    
    return [LocatorMemoryResponse.model_validate(m) for m in memories]


@router.get("/projects/{project_id}/memory/episodes", response_model=List[EpisodeMemoryResponse])
async def list_episodes(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    stmt = select(EpisodeMemory).where(EpisodeMemory.project_id == project_id).order_by(EpisodeMemory.created_at.desc())
    result = await db.execute(stmt)
    memories = result.scalars().all()
    
    return [EpisodeMemoryResponse.model_validate(m) for m in memories]


@router.get("/projects/{project_id}/memory/failure-patterns", response_model=List[FailurePatternResponse])
async def list_failure_patterns(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    stmt = select(FailurePattern).where(FailurePattern.project_id == project_id).order_by(FailurePattern.frequency.desc())
    result = await db.execute(stmt)
    patterns = result.scalars().all()
    
    return [FailurePatternResponse.model_validate(p) for p in patterns]


@router.get("/projects/{project_id}/memory/visual-baselines", response_model=List[VisualBaselineResponse])
async def list_visual_baselines_memory(
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


@router.post("/projects/{project_id}/memory/search", response_model=SearchMemoryResponse)
async def search_memory(
    project_id: UUID,
    request: SearchMemoryRequest,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = request.query.lower()
    types = request.types or ["locator", "episode", "failure_pattern", "visual_baseline"]
    limit = request.limit
    
    response = SearchMemoryResponse()
    
    if "locator" in types:
        stmt = select(LocatorMemory).where(
            LocatorMemory.project_id == project_id,
            or_(
                LocatorMemory.selector.ilike(f"%{query}%"),
                LocatorMemory.page_url.ilike(f"%{query}%"),
                LocatorMemory.element_text.ilike(f"%{query}%"),
            )
        ).limit(limit)
        result = await db.execute(stmt)
        response.locators = [LocatorMemoryResponse.model_validate(m) for m in result.scalars().all()]
    
    if "episode" in types:
        stmt = select(EpisodeMemory).where(
            EpisodeMemory.project_id == project_id,
            EpisodeMemory.intent.ilike(f"%{query}%")
        ).limit(limit)
        result = await db.execute(stmt)
        response.episodes = [EpisodeMemoryResponse.model_validate(m) for m in result.scalars().all()]
    
    if "failure_pattern" in types:
        stmt = select(FailurePattern).where(
            FailurePattern.project_id == project_id,
            or_(
                FailurePattern.error_pattern.ilike(f"%{query}%"),
                FailurePattern.step_action.ilike(f"%{query}%"),
                FailurePattern.suggested_fix.ilike(f"%{query}%"),
            )
        ).limit(limit)
        result = await db.execute(stmt)
        response.failure_patterns = [FailurePatternResponse.model_validate(m) for m in result.scalars().all()]
    
    if "visual_baseline" in types:
        stmt = select(VisualBaseline).where(
            VisualBaseline.project_id == project_id,
            VisualBaseline.name.ilike(f"%{query}%")
        ).limit(limit)
        result = await db.execute(stmt)
        response.visual_baselines = [VisualBaselineResponse.model_validate(m) for m in result.scalars().all()]
    
    return response