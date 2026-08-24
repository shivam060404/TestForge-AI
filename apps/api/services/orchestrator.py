"""Orchestrator service for coordinating test execution"""
import asyncio
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.run import TestRun, StepExecution, RunStatus, StepStatus
from models.test_case import TestCase, TestStep
from models.healing import HealingCandidate, HealingStatus
from models.memory import LocatorMemory, EpisodeMemory, EpisodeOutcome, LocatorStrategy
from core.database import async_session_maker
from core.logging import get_logger
from services.playwright_worker import PlaywrightWorker
from services.verifier import Verifier
from services.healer import Healer
from services.design_intelligence import DesignIntelligence
from services.memory import MemoryService

logger = get_logger(__name__)


class Orchestrator:
    """Coordinates test execution, healing, and reporting"""
    
    def __init__(self):
        self.worker = PlaywrightWorker()
        self.verifier = Verifier()
        self.healer = Healer()
        self.design_intelligence = DesignIntelligence()
        self.memory = MemoryService()
    
    async def execute_run(self, run_id: uuid.UUID) -> None:
        """Execute a test run"""
        async with async_session_maker() as db:
            # Load run with test case and environment
            stmt = (
                select(TestRun)
                .options(
                    selectinload(TestRun.test_case).selectinload(TestCase.steps),
                    selectinload(TestRun.environment),
                    selectinload(TestRun.step_executions),
                )
                .where(TestRun.id == run_id)
            )
            result = await db.execute(stmt)
            run = result.scalar_one_or_none()
            
            if not run:
                logger.error("run_not_found", run_id=str(run_id))
                return
            
            if run.status != RunStatus.PENDING:
                logger.warning("run_not_pending", run_id=str(run_id), status=run.status.value)
                return
            
            # Update run status to running
            run.status = RunStatus.RUNNING
            run.started_at = datetime.now(timezone.utc)
            await db.commit()
            
            logger.info("run_started", run_id=str(run_id))
            await self._broadcast(run_id, "run_started", {
                "run_id": str(run_id),
                "test_case_id": str(run.test_case_id),
                "environment_id": str(run.environment_id),
            })
        
        try:
            # Initialize browser
            await self.worker.initialize()
            
            # Execute each step
            passed = 0
            failed = 0
            skipped = 0
            
            async with async_session_maker() as db:
                # Reload run with relationships
                stmt = (
                    select(TestRun)
                    .options(
                        selectinload(TestRun.test_case).selectinload(TestCase.steps),
                        selectinload(TestRun.environment),
                        selectinload(TestRun.step_executions),
                    )
                    .where(TestRun.id == run_id)
                )
                result = await db.execute(stmt)
                run = result.scalar_one()
                
                for step_exec in sorted(run.step_executions, key=lambda x: x.order):
                    step_data = run.test_case.steps[step_exec.order] if step_exec.order < len(run.test_case.steps) else None
                    if not step_data:
                        continue
                    
                    step_result = await self._execute_step(
                        run_id=run_id,
                        step_exec=step_exec,
                        step_data=step_data,
                        environment=run.environment,
                        db=db,
                    )
                    
                    if step_result == StepStatus.PASSED:
                        passed += 1
                    elif step_result == StepStatus.FAILED:
                        failed += 1
                        # Check if we should continue on failure
                        if not step_data.get("continue_on_failure", False):
                            break
                    elif step_result == StepStatus.SKIPPED:
                        skipped += 1
            
            # Update run status
            final_status = RunStatus.PASSED if failed == 0 else RunStatus.FAILED
            await self._finalize_run(run_id, final_status, passed, failed, skipped)
            
            # Run design intelligence checks
            await self.design_intelligence.analyze_run(run_id)
            
            # Store episode in memory
            async with async_session_maker() as db:
                stmt = select(TestRun).where(TestRun.id == run_id)
                result = await db.execute(stmt)
                run = result.scalar_one()
                
                await self.memory.store_episode(
                    project_id=run.project_id,
                    intent=run.test_case.description or run.test_case.name,
                    steps=run.test_case.steps,
                    outcome=EpisodeOutcome.SUCCESS if final_status == RunStatus.PASSED else EpisodeOutcome.FAILURE,
                    run_id=run_id,
                )
            
        except Exception as e:
            logger.error("run_execution_error", run_id=str(run_id), error=str(e))
            await self._finalize_run(run_id, RunStatus.FAILED, 0, 0, 0, str(e))
        finally:
            await self.worker.cleanup()
    
    async def _execute_step(
        self,
        run_id: uuid.UUID,
        step_exec: StepExecution,
        step_data: Dict[str, Any],
        environment: Any,
        db: AsyncSession,
    ) -> StepStatus:
        """Execute a single test step"""
        step_exec.status = StepStatus.RUNNING
        step_exec.started_at = datetime.now(timezone.utc)
        await db.commit()
        
        await self._broadcast(run_id, "step_started", {
            "step_execution_id": str(step_exec.id),
            "step_id": str(step_exec.step_id),
            "order": step_exec.order,
            "action": step_data.get("action"),
            "description": step_data.get("description"),
        })
        
        try:
            # Resolve locator using memory
            locator = step_data.get("locator")
            strategy = step_data.get("locator_strategy", "css")
            
            if locator:
                # Try to get healed locator from memory
                memory_entry = await self.memory.get_locator_memory(
                    project_id=run_id,  # Will be overridden with actual project_id
                    selector=locator,
                    strategy=strategy,
                    page_url=environment.base_url,
                )
                if memory_entry and memory_entry.success_count > memory_entry.failure_count:
                    locator = memory_entry.selector
                    strategy = memory_entry.strategy
            
            # Execute step via Playwright
            result = await self.worker.execute_step(
                action=step_data["action"],
                url=environment.base_url + (step_data.get("target") or ""),
                locator=locator,
                strategy=strategy,
                value=step_data.get("value"),
                options=step_data.get("options", {}),
            )
            
            # Verify assertions
            if step_data.get("assertion"):
                assertion_result = await self.verifier.verify(
                    page=self.worker.page,
                    assertion=step_data["assertion"],
                    locator=locator,
                    strategy=strategy,
                )
                if not assertion_result.passed:
                    raise AssertionError(assertion_result.message)
            
            # Capture evidence
            screenshot_path = await self.worker.capture_screenshot(run_id, step_exec.id)
            dom_snapshot_path = await self.worker.capture_dom_snapshot(run_id, step_exec.id)
            console_logs = await self.worker.get_console_logs()
            network_logs = await self.worker.get_network_logs()
            trace_path = await self.worker.stop_tracing(run_id, step_exec.id)
            
            step_exec.status = StepStatus.PASSED
            step_exec.finished_at = datetime.now(timezone.utc)
            step_exec.duration_ms = int((step_exec.finished_at - step_exec.started_at).total_seconds() * 1000)
            step_exec.screenshot_path = screenshot_path
            step_exec.dom_snapshot_path = dom_snapshot_path
            step_exec.console_logs = console_logs
            step_exec.network_logs = network_logs
            step_exec.trace_path = trace_path
            
            await db.commit()
            
            # Update locator memory on success
            if locator:
                await self.memory.record_locator_success(
                    project_id=run.project_id,
                    selector=locator,
                    strategy=strategy,
                    page_url=environment.base_url,
                )
            
            await self._broadcast(run_id, "step_completed", {
                "step_execution_id": str(step_exec.id),
                "status": StepStatus.PASSED.value,
                "duration_ms": step_exec.duration_ms,
                "screenshot_path": screenshot_path,
            })
            
            return StepStatus.PASSED
            
        except Exception as e:
            step_exec.status = StepStatus.FAILED
            step_exec.finished_at = datetime.now(timezone.utc)
            step_exec.duration_ms = int((step_exec.finished_at - step_exec.started_at).total_seconds() * 1000)
            step_exec.error = str(e)
            
            # Capture failure evidence
            step_exec.screenshot_path = await self.worker.capture_screenshot(run_id, step_exec.id)
            step_exec.dom_snapshot_path = await self.worker.capture_dom_snapshot(run_id, step_exec.id)
            step_exec.console_logs = await self.worker.get_console_logs()
            step_exec.network_logs = await self.worker.get_network_logs()
            step_exec.trace_path = await self.worker.stop_tracing(run_id, step_exec.id)
            
            await db.commit()
            
            # Update locator memory on failure
            if locator:
                await self.memory.record_locator_failure(
                    project_id=run.project_id,
                    selector=locator,
                    strategy=strategy,
                    page_url=environment.base_url,
                )
            
            # Attempt healing
            if step_data.get("action") in ("click", "fill", "hover", "check", "uncheck", "select"):
                healing_candidate = await self.healer.generate_candidate(
                    run_id=run_id,
                    step_execution_id=step_exec.id,
                    original_locator=locator or "",
                    original_strategy=strategy,
                    error=str(e),
                    page=self.worker.page,
                )
                
                if healing_candidate:
                    db.add(healing_candidate)
                    await db.commit()
                    
                    step_exec.healing_candidate_id = healing_candidate.id
                    await db.commit()
                    
                    await self._broadcast(run_id, "healing_candidate", {
                        "candidate": {
                            "id": str(healing_candidate.id),
                            "run_id": str(healing_candidate.run_id),
                            "step_execution_id": str(healing_candidate.step_execution_id),
                            "original_locator": healing_candidate.original_locator,
                            "original_strategy": healing_candidate.original_strategy,
                            "suggested_locator": healing_candidate.suggested_locator,
                            "suggested_strategy": healing_candidate.suggested_strategy,
                            "confidence": healing_candidate.confidence,
                            "reasoning": healing_candidate.reasoning,
                            "status": healing_candidate.status.value,
                            "created_at": healing_candidate.created_at.isoformat(),
                        }
                    })
            
            await self._broadcast(run_id, "step_failed", {
                "step_execution_id": str(step_exec.id),
                "error": str(e),
                "healing_candidate": {
                    "id": str(step_exec.healing_candidate_id),
                } if step_exec.healing_candidate_id else None,
            })
            
            return StepStatus.FAILED
    
    async def _finalize_run(
        self,
        run_id: uuid.UUID,
        status: RunStatus,
        passed: int,
        failed: int,
        skipped: int,
        error: Optional[str] = None,
    ) -> None:
        """Finalize run with status and metrics"""
        async with async_session_maker() as db:
            run = await db.get(TestRun, run_id)
            if not run:
                return
            
            run.status = status
            run.finished_at = datetime.now(timezone.utc)
            if run.started_at:
                run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
            run.passed_steps = passed
            run.failed_steps = failed
            run.skipped_steps = skipped
            
            await db.commit()
            
            await self._broadcast(run_id, "run_completed", {
                "run_id": str(run_id),
                "status": status.value,
                "duration_ms": run.duration_ms,
                "passed_steps": passed,
                "failed_steps": failed,
            })
            
            logger.info("run_completed", run_id=str(run_id), status=status.value)
    
    async def _broadcast(self, run_id: uuid.UUID, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast event to SSE subscribers"""
        from api.routes.runs import _event_subscribers
        if run_id in _event_subscribers:
            event = {
                "type": event_type,
                "run_id": str(run_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data,
            }
            for queue in _event_subscribers[run_id]:
                await queue.put(json.dumps(event))


orchestrator = Orchestrator()