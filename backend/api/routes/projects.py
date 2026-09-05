from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.project import Project
from models.environment import Environment
from models.test_case import TestCase, TestStep
from models.run import TestRun, StepExecution, RunStatus, StepStatus
from models.healing import HealingCandidate, HealingStatus
from models.design import VisualBaseline, VisualComparison, AccessibilityIssue
from models.memory import LocatorMemory, EpisodeMemory, FailurePattern
from schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse,
    TestCaseCreate, TestCaseUpdate, TestCaseResponse, GenerateTestCaseRequest, TestStepCreate, TestStepResponse,
    TestRunCreate, TestRunResponse, TestRunDetailResponse, StepExecutionResponse,
    HealingCandidateResponse, ApproveHealingRequest,
    VisualBaselineResponse, VisualComparisonResponse, AccessibilityIssueResponse, DesignInsightResponse,
    LocatorMemoryResponse, EpisodeMemoryResponse, FailurePatternResponse, SearchMemoryRequest, SearchMemoryResponse,
    PaginationParams, PaginatedResponse,
)
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ============================================
# Projects
# ============================================

@router.get("/projects", response_model=PaginatedResponse)
async def list_projects(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Project).order_by(Project.created_at.desc())
    count_stmt = select(func.count()).select_from(Project)
    
    total = await db.scalar(count_stmt)
    result = await db.execute(
        stmt.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    )
    projects = result.scalars().all()
    
    return PaginatedResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    project = Project(**project_in.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    logger.info("project_created", project_id=str(project.id))
    return ProjectResponse.model_validate(project)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for field, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()
    logger.info("project_deleted", project_id=str(project_id))