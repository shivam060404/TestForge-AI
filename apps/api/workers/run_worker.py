"""Background worker for processing test runs"""
import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_maker
from core.logging import get_logger, configure_logging
from core.config import settings
from models.run import TestRun, RunStatus
from services.orchestrator import orchestrator

logger = get_logger(__name__)


class RunWorker:
    """Processes test runs from the queue"""
    
    def __init__(self):
        self.running = False
        self.poll_interval = 5  # seconds
    
    async def start(self):
        """Start the worker loop"""
        self.running = True
        logger.info("worker_started")
        
        while self.running:
            try:
                await self._process_pending_runs()
            except Exception as e:
                logger.error("worker_error", error=str(e))
            
            await asyncio.sleep(self.poll_interval)
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        logger.info("worker_stopped")
    
    async def _process_pending_runs(self):
        """Find and execute pending runs"""
        async with async_session_maker() as db:
            stmt = select(TestRun).where(
                TestRun.status == RunStatus.PENDING
            ).order_by(TestRun.created_at).limit(1)
            
            result = await db.execute(stmt)
            run = result.scalar_one_or_none()
            
            if run:
                logger.info("worker_picked_run", run_id=str(run.id))
                # Execute run in background
                asyncio.create_task(self._execute_run(run.id))
    
    async def _execute_run(self, run_id: uuid.UUID):
        """Execute a single run"""
        try:
            await orchestrator.execute_run(run_id)
        except Exception as e:
            logger.error("run_execution_failed", run_id=str(run_id), error=str(e))
            # Mark run as failed
            async with async_session_maker() as db:
                run = await db.get(TestRun, run_id)
                if run:
                    run.status = RunStatus.FAILED
                    run.finished_at = datetime.now(timezone.utc)
                    if run.started_at:
                        run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
                    await db.commit()


async def main():
    configure_logging(settings.log_level)
    worker = RunWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())