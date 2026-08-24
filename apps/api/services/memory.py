"""Memory service for persistent learning"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.memory import LocatorMemory, EpisodeMemory, FailurePattern, LocatorStrategy, EpisodeOutcome
from core.database import async_session_maker
from core.logging import get_logger

logger = get_logger(__name__)


class MemoryService:
    """Manages persistent memory for locators, episodes, and failure patterns"""
    
    async def record_locator_success(
        self,
        project_id: uuid.UUID,
        selector: str,
        strategy: str,
        page_url: str,
        element_role: Optional[str] = None,
        element_text: Optional[str] = None,
    ) -> None:
        """Record successful locator usage"""
        async with async_session_maker() as db:
            stmt = select(LocatorMemory).where(
                LocatorMemory.project_id == project_id,
                LocatorMemory.selector == selector,
                LocatorMemory.strategy == strategy,
                LocatorMemory.page_url == page_url,
            )
            result = await db.execute(stmt)
            memory = result.scalar_one_or_none()
            
            if memory:
                memory.success_count += 1
                memory.last_used_at = datetime.now(timezone.utc)
            else:
                memory = LocatorMemory(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    selector=selector,
                    strategy=strategy,
                    page_url=page_url,
                    element_role=element_role,
                    element_text=element_text,
                    success_count=1,
                    failure_count=0,
                    last_used_at=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(memory)
            
            await db.commit()
    
    async def record_locator_failure(
        self,
        project_id: uuid.UUID,
        selector: str,
        strategy: str,
        page_url: str,
        element_role: Optional[str] = None,
        element_text: Optional[str] = None,
    ) -> None:
        """Record failed locator usage"""
        async with async_session_maker() as db:
            stmt = select(LocatorMemory).where(
                LocatorMemory.project_id == project_id,
                LocatorMemory.selector == selector,
                LocatorMemory.strategy == strategy,
                LocatorMemory.page_url == page_url,
            )
            result = await db.execute(stmt)
            memory = result.scalar_one_or_none()
            
            if memory:
                memory.failure_count += 1
                memory.last_used_at = datetime.now(timezone.utc)
            else:
                memory = LocatorMemory(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    selector=selector,
                    strategy=strategy,
                    page_url=page_url,
                    element_role=element_role,
                    element_text=element_text,
                    success_count=0,
                    failure_count=1,
                    last_used_at=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(memory)
            
            await db.commit()
    
    async def get_locator_memory(
        self,
        project_id: uuid.UUID,
        selector: str,
        strategy: str,
        page_url: str,
    ) -> Optional[LocatorMemory]:
        """Get locator memory entry"""
        async with async_session_maker() as db:
            stmt = select(LocatorMemory).where(
                LocatorMemory.project_id == project_id,
                LocatorMemory.selector == selector,
                LocatorMemory.strategy == strategy,
                LocatorMemory.page_url == page_url,
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_similar_locator(
        self,
        project_id: uuid.UUID,
        original_locator: str,
        page_url: str,
    ) -> Optional[LocatorMemory]:
        """Find similar locator from memory"""
        async with async_session_maker() as db:
            # Look for successful locators on the same page
            stmt = select(LocatorMemory).where(
                LocatorMemory.project_id == project_id,
                LocatorMemory.page_url == page_url,
                LocatorMemory.success_count > LocatorMemory.failure_count,
            ).order_by(
                (LocatorMemory.success_count - LocatorMemory.failure_count).desc()
            ).limit(5)
            
            result = await db.execute(stmt)
            memories = result.scalars().all()
            
            # Simple similarity: check if original locator text is contained in memory
            for memory in memories:
                if (original_locator.lower() in memory.selector.lower() or 
                    memory.selector.lower() in original_locator.lower() or
                    (memory.element_text and original_locator.lower() in memory.element_text.lower())):
                    return memory
            
            return None
    
    async def store_episode(
        self,
        project_id: uuid.UUID,
        intent: str,
        steps: List[Dict[str, Any]],
        outcome: EpisodeOutcome,
        run_id: Optional[uuid.UUID] = None,
    ) -> None:
        """Store test episode in memory"""
        async with async_session_maker() as db:
            episode = EpisodeMemory(
                id=uuid.uuid4(),
                project_id=project_id,
                intent=intent,
                steps=steps,
                outcome=outcome,
                run_id=run_id,
                created_at=datetime.now(timezone.utc),
            )
            db.add(episode)
            await db.commit()
    
    async def record_failure_pattern(
        self,
        project_id: uuid.UUID,
        error_pattern: str,
        step_action: str,
        suggested_fix: Optional[str] = None,
    ) -> None:
        """Record or update failure pattern"""
        async with async_session_maker() as db:
            stmt = select(FailurePattern).where(
                FailurePattern.project_id == project_id,
                FailurePattern.error_pattern == error_pattern,
                FailurePattern.step_action == step_action,
            )
            result = await db.execute(stmt)
            pattern = result.scalar_one_or_none()
            
            if pattern:
                pattern.frequency += 1
                pattern.last_seen_at = datetime.now(timezone.utc)
                if suggested_fix and not pattern.suggested_fix:
                    pattern.suggested_fix = suggested_fix
            else:
                pattern = FailurePattern(
                    id=uuid.uuid4(),
                    project_id=project_id,
                    error_pattern=error_pattern,
                    step_action=step_action,
                    frequency=1,
                    suggested_fix=suggested_fix,
                    last_seen_at=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                )
                db.add(pattern)
            
            await db.commit()
    
    async def search_memory(
        self,
        project_id: uuid.UUID,
        query: str,
        types: Optional[List[str]] = None,
        limit: int = 20,
    ) -> Dict[str, List[Any]]:
        """Search across all memory types"""
        types = types or ["locator", "episode", "failure_pattern", "visual_baseline"]
        query_lower = query.lower()
        results = {
            "locators": [],
            "episodes": [],
            "failure_patterns": [],
            "visual_baselines": [],
        }
        
        async with async_session_maker() as db:
            if "locator" in types:
                stmt = select(LocatorMemory).where(
                    LocatorMemory.project_id == project_id,
                    or_(
                        LocatorMemory.selector.ilike(f"%{query_lower}%"),
                        LocatorMemory.page_url.ilike(f"%{query_lower}%"),
                        LocatorMemory.element_text.ilike(f"%{query_lower}%"),
                    )
                ).limit(limit)
                result = await db.execute(stmt)
                results["locators"] = result.scalars().all()
            
            if "episode" in types:
                stmt = select(EpisodeMemory).where(
                    EpisodeMemory.project_id == project_id,
                    EpisodeMemory.intent.ilike(f"%{query_lower}%")
                ).limit(limit)
                result = await db.execute(stmt)
                results["episodes"] = result.scalars().all()
            
            if "failure_pattern" in types:
                stmt = select(FailurePattern).where(
                    FailurePattern.project_id == project_id,
                    or_(
                        FailurePattern.error_pattern.ilike(f"%{query_lower}%"),
                        FailurePattern.step_action.ilike(f"%{query_lower}%"),
                        FailurePattern.suggested_fix.ilike(f"%{query_lower}%"),
                    )
                ).limit(limit)
                result = await db.execute(stmt)
                results["failure_patterns"] = result.scalars().all()
            
            if "visual_baseline" in types:
                from models.design import VisualBaseline
                stmt = select(VisualBaseline).where(
                    VisualBaseline.project_id == project_id,
                    VisualBaseline.name.ilike(f"%{query_lower}%")
                ).limit(limit)
                result = await db.execute(stmt)
                results["visual_baselines"] = result.scalars().all()
        
        return results
    
    async def get_episodes_for_intent(
        self,
        project_id: uuid.UUID,
        intent: str,
        limit: int = 5,
    ) -> List[EpisodeMemory]:
        """Get similar episodes for planning"""
        async with async_session_maker() as db:
            stmt = select(EpisodeMemory).where(
                EpisodeMemory.project_id == project_id,
                EpisodeMemory.intent.ilike(f"%{intent}%"),
                EpisodeMemory.outcome == EpisodeOutcome.SUCCESS,
            ).order_by(EpisodeMemory.created_at.desc()).limit(limit)
            
            result = await db.execute(stmt)
            return result.scalars().all()
    
    async def get_failure_patterns(
        self,
        project_id: uuid.UUID,
        step_action: Optional[str] = None,
        limit: int = 20,
    ) -> List[FailurePattern]:
        """Get failure patterns for a project"""
        async with async_session_maker() as db:
            stmt = select(FailurePattern).where(
                FailurePattern.project_id == project_id,
            ).order_by(FailurePattern.frequency.desc()).limit(limit)
            
            if step_action:
                stmt = stmt.where(FailurePattern.step_action == step_action)
            
            result = await db.execute(stmt)
            return result.scalars().all()


memory_service = MemoryService()