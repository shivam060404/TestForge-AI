"""Design Intelligence service for visual regression and accessibility checks"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
import base64

import cv2
import numpy as np
from playwright.async_api import Page

from models.design import VisualBaseline, VisualComparison, AccessibilityIssue, AccessibilityImpact
from core.database import async_session_maker
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class DesignIntelligence:
    """Visual regression and accessibility analysis"""
    
    def __init__(self):
        self.artifacts_dir = Path(settings.artifacts_dir)
        self.visual_threshold = 0.1  # 10% difference threshold
    
    async def analyze_run(self, run_id: uuid.UUID) -> None:
        """Analyze a completed run for visual and accessibility issues"""
        async with async_session_maker() as db:
            from models.run import TestRun, StepExecution
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            
            stmt = (
                select(TestRun)
                .options(selectinload(TestRun.step_executions))
                .where(TestRun.id == run_id)
            )
            result = await db.execute(stmt)
            run = result.scalar_one_or_none()
            
            if not run:
                return
            
            # Get visual baselines for this project
            vb_stmt = select(VisualBaseline).where(VisualBaseline.project_id == run.project_id)
            vb_result = await db.execute(vb_stmt)
            baselines = vb_result.scalars().all()
            
            # Compare screenshots against baselines
            for step_exec in run.step_executions:
                if step_exec.screenshot_path:
                    for baseline in baselines:
                        await self._compare_screenshot(
                            db=db,
                            baseline=baseline,
                            run_id=run_id,
                            step_execution_id=step_exec.id,
                            screenshot_path=step_exec.screenshot_path,
                        )
                
                # Run accessibility checks
                await self._check_accessibility(db, run_id, step_exec.id)
    
    async def _compare_screenshot(
        self,
        db,
        baseline: VisualBaseline,
        run_id: uuid.UUID,
        step_execution_id: uuid.UUID,
        screenshot_path: str,
    ) -> None:
        """Compare screenshot against visual baseline"""
        try:
            # Load images
            baseline_img = cv2.imread(baseline.image_path)
            current_img = cv2.imread(screenshot_path)
            
            if baseline_img is None or current_img is None:
                logger.warning("image_load_failed", baseline=baseline.image_path, current=screenshot_path)
                return
            
            # Resize current to match baseline if needed
            if current_img.shape != baseline_img.shape:
                current_img = cv2.resize(current_img, (baseline_img.shape[1], baseline_img.shape[0]))
            
            # Calculate difference
            diff = cv2.absdiff(baseline_img, current_img)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # Threshold the difference
            _, thresh = cv2.threshold(diff_gray, 30, 255, cv2.THRESH_BINARY)
            
            # Calculate difference percentage
            total_pixels = thresh.shape[0] * thresh.shape[1]
            diff_pixels = cv2.countNonZero(thresh)
            difference_percent = (diff_pixels / total_pixels) * 100
            
            match = difference_percent <= (self.visual_threshold * 100)
            
            # Save diff image if there's a difference
            diff_image_path = None
            if not match:
                diff_filename = f"diff_{run_id}_{step_execution_id}_{baseline.id}.png"
                diff_path = self.artifacts_dir / "diffs" / diff_filename
                diff_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(diff_path), diff)
                diff_image_path = str(diff_path)
            
            # Store comparison result
            comparison = VisualComparison(
                id=uuid.uuid4(),
                baseline_id=baseline.id,
                run_id=run_id,
                step_execution_id=step_execution_id,
                match=match,
                difference_percent=difference_percent,
                diff_image_path=diff_image_path,
                threshold=self.visual_threshold,
                created_at=datetime.now(timezone.utc),
            )
            db.add(comparison)
            await db.commit()
            
            logger.info(
                "visual_comparison_completed",
                baseline_id=str(baseline.id),
                run_id=str(run_id),
                match=match,
                difference_percent=difference_percent,
            )
            
        except Exception as e:
            logger.error("visual_comparison_error", error=str(e))
    
    async def _check_accessibility(
        self,
        db,
        run_id: uuid.UUID,
        step_execution_id: uuid.UUID,
    ) -> None:
        """Run accessibility checks using axe-core"""
        # This would typically inject axe-core into the page and run checks
        # For now, we'll simulate some common accessibility issues
        
        # In a real implementation, you would:
        # 1. Inject axe-core script into the page
        # 2. Run axe.run() 
        # 3. Parse results and store as AccessibilityIssue records
        
        # Simulated issues for demo
        simulated_issues = [
            {
                "rule_id": "color-contrast",
                "impact": AccessibilityImpact.SERIOUS,
                "description": "Insufficient color contrast ratio",
                "help": "Ensure text has a contrast ratio of at least 4.5:1",
                "selector": "button.primary",
            },
            {
                "rule_id": "label",
                "impact": AccessibilityImpact.CRITICAL,
                "description": "Form element missing label",
                "help": "Add a label element or aria-label attribute",
                "selector": "input[type='email']",
            },
        ]
        
        for issue in simulated_issues:
            ai = AccessibilityIssue(
                id=uuid.uuid4(),
                run_id=run_id,
                step_execution_id=step_execution_id,
                rule_id=issue["rule_id"],
                impact=issue["impact"],
                description=issue["description"],
                help=issue["help"],
                selector=issue["selector"],
                created_at=datetime.now(timezone.utc),
            )
            db.add(ai)
        
        await db.commit()
    
    async def create_baseline_from_run(
        self,
        project_id: uuid.UUID,
        run_id: uuid.UUID,
        name: str,
        step_execution_id: uuid.UUID,
    ) -> Optional[VisualBaseline]:
        """Create a visual baseline from a successful run step"""
        async with async_session_maker() as db:
            from models.run import StepExecution
            from sqlalchemy import select
            
            stmt = select(StepExecution).where(StepExecution.id == step_execution_id)
            result = await db.execute(stmt)
            step_exec = result.scalar_one_or_none()
            
            if not step_exec or not step_exec.screenshot_path:
                return None
            
            # Copy screenshot to baseline location
            baseline_filename = f"{name}_{uuid.uuid4().hex[:8]}.png"
            baseline_path = self.artifacts_dir / "baselines" / baseline_filename
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(step_exec.screenshot_path, baseline_path)
            
            # Get viewport from page (would need to be stored)
            baseline = VisualBaseline(
                id=uuid.uuid4(),
                project_id=project_id,
                name=name,
                viewport_width=1280,
                viewport_height=720,
                image_path=str(baseline_path),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(baseline)
            await db.commit()
            
            return baseline


design_intelligence = DesignIntelligence()