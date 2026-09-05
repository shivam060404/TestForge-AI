from typing import List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.project import Project
from models.test_case import TestCase
from models.environment import Environment
from schemas import (
    TestCaseCreate, TestCaseUpdate, TestCaseResponse,
    GenerateTestCaseRequest, PaginationParams, PaginatedResponse,
)
from services.planner import planner
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/projects/{project_id}/test-cases", response_model=PaginatedResponse)
async def list_test_cases(
    project_id: UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt = select(TestCase).where(TestCase.project_id == project_id).order_by(TestCase.created_at.desc())
    count_stmt = select(func.count()).select_from(TestCase).where(TestCase.project_id == project_id)

    total = await db.scalar(count_stmt)
    result = await db.execute(
        stmt.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    )
    test_cases = result.scalars().all()

    return PaginatedResponse(
        items=[TestCaseResponse.model_validate(tc) for tc in test_cases],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.post("/projects/{project_id}/test-cases", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    project_id: UUID,
    tc_in: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if tc_in.environment_id:
        env = await db.get(Environment, tc_in.environment_id)
        if not env or env.project_id != project_id:
            raise HTTPException(status_code=404, detail="Environment not found")

    steps_data = []
    for i, step in enumerate(tc_in.steps):
        step_dict = step.model_dump()
        step_dict["id"] = str(uuid4())
        step_dict["order"] = i
        steps_data.append(step_dict)

    test_case = TestCase(
        project_id=project_id,
        environment_id=tc_in.environment_id,
        name=tc_in.name,
        description=tc_in.description,
        steps=steps_data,
        tags=tc_in.tags,
    )
    db.add(test_case)
    await db.commit()
    await db.refresh(test_case)
    logger.info("test_case_created", test_case_id=str(test_case.id), project_id=str(project_id))
    return TestCaseResponse.model_validate(test_case)


@router.post("/projects/{project_id}/test-cases/generate", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def generate_test_case(
    project_id: UUID,
    request: GenerateTestCaseRequest,
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if request.environment_id:
        env = await db.get(Environment, request.environment_id)
        if not env or env.project_id != project_id:
            raise HTTPException(status_code=404, detail="Environment not found")

    # Generate steps via planner (pattern -> memory -> Groq LLM fallback chain)
    planned_steps = await planner.generate_steps(
        intent=request.intent,
        project_id=project_id,
        environment_id=request.environment_id,
        context=request.context,
    )

    validation_errors = planner.validate_steps(planned_steps)
    if validation_errors:
        logger.warning("generated_steps_validation_issues", errors=validation_errors)

    steps_data = []
    for i, step in enumerate(planned_steps):
        steps_data.append({
            "id": str(uuid4()),
            "order": i,
            "action": step.action,
            "target": step.target,
            "locator": step.locator,
            "locator_strategy": step.locator_strategy,
            "value": step.value,
            "options": step.options or {},
            "assertion": step.assertion,
            "description": step.description,
            "continue_on_failure": step.continue_on_failure,
        })

    test_case = TestCase(
        project_id=project_id,
        environment_id=request.environment_id,
        name=f"Generated: {request.intent[:60]}",
        description=request.intent,
        steps=steps_data,
        tags=["generated"],
    )
    db.add(test_case)
    await db.commit()
    await db.refresh(test_case)
    logger.info("test_case_generated", test_case_id=str(test_case.id), project_id=str(project_id), step_count=len(steps_data))
    return TestCaseResponse.model_validate(test_case)


@router.get("/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(
    test_case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    test_case = await db.get(TestCase, test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return TestCaseResponse.model_validate(test_case)


@router.patch("/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(
    test_case_id: UUID,
    tc_in: TestCaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    test_case = await db.get(TestCase, test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    update_data = tc_in.model_dump(exclude_unset=True)
    if "steps" in update_data and update_data["steps"] is not None:
        update_data["steps"] = [
            {**s, "id": str(uuid4()), "order": i} if not s.get("id") else {**s, "order": i}
            for i, s in enumerate(update_data["steps"])
        ]

    for field, value in update_data.items():
        setattr(test_case, field, value)

    await db.commit()
    await db.refresh(test_case)
    return TestCaseResponse.model_validate(test_case)


@router.delete("/test-cases/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    test_case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    test_case = await db.get(TestCase, test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    await db.delete(test_case)
    await db.commit()
    logger.info("test_case_deleted", test_case_id=str(test_case_id))