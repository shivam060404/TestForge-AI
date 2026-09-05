from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.project import Project
from models.environment import Environment
from schemas import (
    EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse,
    PaginationParams, PaginatedResponse,
)
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/projects/{project_id}/environments", response_model=PaginatedResponse)
async def list_environments(
    project_id: UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    stmt = select(Environment).where(Environment.project_id == project_id).order_by(Environment.created_at.desc())
    count_stmt = select(func.count()).select_from(Environment).where(Environment.project_id == project_id)
    
    total = await db.scalar(count_stmt)
    result = await db.execute(
        stmt.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    )
    environments = result.scalars().all()
    
    return PaginatedResponse(
        items=[EnvironmentResponse.model_validate(e) for e in environments],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.post("/projects/{project_id}/environments", response_model=EnvironmentResponse, status_code=status.HTTP_201_CREATED)
async def create_environment(
    project_id: UUID,
    env_in: EnvironmentCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    data = env_in.model_dump()
    data["base_url"] = str(data["base_url"])
    env = Environment(project_id=project_id, **data)
    db.add(env)
    await db.commit()
    await db.refresh(env)
    logger.info("environment_created", environment_id=str(env.id), project_id=str(project_id))
    return EnvironmentResponse.model_validate(env)


@router.get("/environments/{environment_id}", response_model=EnvironmentResponse)
async def get_environment(
    environment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    env = await db.get(Environment, environment_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return EnvironmentResponse.model_validate(env)


@router.patch("/environments/{environment_id}", response_model=EnvironmentResponse)
async def update_environment(
    environment_id: UUID,
    env_in: EnvironmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    env = await db.get(Environment, environment_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    
    for field, value in env_in.model_dump(exclude_unset=True).items():
        if field == "base_url" and value:
            value = str(value)
        setattr(env, field, value)
    
    await db.commit()
    await db.refresh(env)
    return EnvironmentResponse.model_validate(env)


@router.delete("/environments/{environment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(
    environment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    env = await db.get(Environment, environment_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    
    await db.delete(env)
    await db.commit()
    logger.info("environment_deleted", environment_id=str(environment_id))