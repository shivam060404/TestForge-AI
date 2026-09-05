import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import engine, async_session_maker, Base
from models.project import Project
from models.environment import Environment
from models.test_case import TestCase, TestStep
from core.logging import configure_logging, get_logger

configure_logging("INFO")
logger = get_logger(__name__)


async def seed_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as session:
        # Create demo project
        project = Project(
            id=uuid.uuid4(),
            name="E-commerce Demo",
            description="Demo project for autonomous QA agent",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(project)
        await session.flush()
        
        # Create environments
        env_staging = Environment(
            id=uuid.uuid4(),
            project_id=project.id,
            name="Staging",
            base_url="https://demo.playwright.dev/todomvc",
            variables={"ENV": "staging"},
            headers={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        env_prod = Environment(
            id=uuid.uuid4(),
            project_id=project.id,
            name="Production",
            base_url="https://example.com",
            variables={"ENV": "production"},
            headers={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add_all([env_staging, env_prod])
        await session.flush()
        
        # Create test case with steps
        test_case = TestCase(
            id=uuid.uuid4(),
            project_id=project.id,
            name="Complete Todo Flow",
            description="Add, complete, and filter todos",
            tags=["smoke", "critical"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(test_case)
        await session.flush()
        
        steps = [
            TestStep(
                id=uuid.uuid4(),
                test_case_id=test_case.id,
                order=0,
                action="goto",
                target="/",
                description="Navigate to todo app",
            ),
            TestStep(
                id=uuid.uuid4(),
                test_case_id=test_case.id,
                order=1,
                action="fill",
                locator='[data-testid="new-todo"]',
                locator_strategy="css",
                value="Learn Playwright",
                description="Add first todo",
            ),
            TestStep(
                id=uuid.uuid4(),
                test_case_id=test_case.id,
                order=2,
                action="press",
                locator='[data-testid="new-todo"]',
                locator_strategy="css",
                value="Enter",
                description="Submit first todo",
            ),
            TestStep(
                id=uuid.uuid4(),
                test_case_id=test_case.id,
                order=3,
                action="fill",
                locator='[data-testid="new-todo"]',
                locator_strategy="css",
                value="Write tests",
                description="Add second todo",
            ),
            TestStep(
                id=uuid.uuid4(),
                test_case_id=test_case.id,
                order=4,
                action="press",
                locator='[data-testid="new-todo"]',
                locator_strategy="css",
                value="Enter",
                description="Submit second todo",
            ),
            TestStep(
                id=uuid.uuid4(),
                test_case_id=test_case.id,
                order=5,
                action="click",
                locator='[data-testid="todo-item"]:first-child [data-testid="toggle"]',
                locator_strategy="css",
                description="Complete first todo",
            ),
            TestStep(
                id=uuid.uuid4(),
                test_case_id=test_case.id,
                order=6,
                action="click",
                locator='[data-testid="filter-active"]',
                locator_strategy="css",
                description="Filter active todos",
            ),
            TestStep(
                id=uuid.uuid4(),
                test_case_id=test_case.id,
                order=7,
                action="assert",
                locator='[data-testid="todo-count"]',
                locator_strategy="css",
                assertion={"type": "text", "expected": "1 item left", "operator": "contains"},
                description="Verify active count",
            ),
        ]
        session.add_all(steps)
        
        await session.commit()
        logger.info("seed_completed", project_id=str(project.id), test_case_id=str(test_case.id))


if __name__ == "__main__":
    asyncio.run(seed_database())