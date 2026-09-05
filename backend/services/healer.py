"""Healer service for self-healing locators"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from playwright.async_api import Page

from models.healing import HealingCandidate, HealingStatus
from models.memory import LocatorMemory, LocatorStrategy
from core.database import async_session_maker
from core.logging import get_logger
from services.memory import MemoryService

logger = get_logger(__name__)


class Healer:
    """Generates healing candidates for failed locators"""
    
    def __init__(self):
        self.memory = MemoryService()
        self.strategies = [
            LocatorStrategy.CSS,
            LocatorStrategy.XPATH,
            LocatorStrategy.TEXT,
            LocatorStrategy.ROLE,
            LocatorStrategy.TEST_ID,
            LocatorStrategy.ID,
            LocatorStrategy.NAME,
            LocatorStrategy.PLACEHOLDER,
            LocatorStrategy.LABEL,
        ]
    
    async def generate_candidate(
        self,
        run_id: uuid.UUID,
        step_execution_id: uuid.UUID,
        project_id: uuid.UUID,
        original_locator: str,
        original_strategy: str,
        error: str,
        page: Page,
    ) -> Optional[HealingCandidate]:
        """Generate a healing candidate for a failed step"""
        
        # Try to find alternative locators
        candidates = await self._find_alternative_locators(
            page=page,
            original_locator=original_locator,
            original_strategy=original_strategy,
            error=error,
        )
        
        if not candidates:
            logger.warning("no_healing_candidates_found", original_locator=original_locator)
            return None
        
        # Score candidates
        scored_candidates = await self._score_candidates(candidates, page)
        
        # Pick best candidate
        best = scored_candidates[0]
        
        # Check if we have memory for this
        memory_match = await self.memory.find_similar_locator(
            project_id=project_id,
            original_locator=original_locator,
            page_url=page.url,
        )
        
        if memory_match:
            best["locator"] = memory_match.selector
            best["strategy"] = memory_match.strategy
            best["confidence"] = min(best["confidence"] + 0.2, 1.0)
            best["reasoning"] += f" (matched from memory: {memory_match.success_count} successes)"
        
        candidate = HealingCandidate(
            id=uuid.uuid4(),
            run_id=run_id,
            step_execution_id=step_execution_id,
            original_locator=original_locator,
            original_strategy=original_strategy,
            suggested_locator=best["locator"],
            suggested_strategy=str(getattr(best["strategy"], "value", best["strategy"])),
            confidence=best["confidence"],
            reasoning=best.get("reasoning", best.get("reason", "")),
            status=HealingStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        
        logger.info(
            "healing_candidate_generated",
            candidate_id=str(candidate.id),
            original_locator=original_locator,
            suggested_locator=candidate.suggested_locator,
            confidence=candidate.confidence,
        )
        
        return candidate
    
    async def _find_alternative_locators(
        self,
        page: Page,
        original_locator: str,
        original_strategy: str,
        error: str,
    ) -> List[Dict[str, Any]]:
        """Find alternative locators for the failed element"""
        candidates = []
        
        try:
            # Try to find element with original locator first
            element = await self._try_locator(page, original_locator, original_strategy)
            
            if element:
                # Get element properties
                tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                element_id = await element.get_attribute("id")
                element_class = await element.get_attribute("class")
                element_text = await element.text_content()
                element_role = await element.evaluate("el => el.getAttribute('role')")
                test_id = await element.get_attribute("data-testid")
                placeholder = await element.get_attribute("placeholder")
                name = await element.get_attribute("name")
                label = await element.evaluate("el => el.labels?.[0]?.textContent")
                
                # Generate candidates based on available attributes
                if test_id:
                    candidates.append({
                        "locator": test_id,
                        "strategy": LocatorStrategy.TEST_ID,
                        "reason": "data-testid attribute",
                    })
                
                if element_id:
                    candidates.append({
                        "locator": element_id,
                        "strategy": LocatorStrategy.ID,
                        "reason": "id attribute",
                    })
                
                if element_role:
                    candidates.append({
                        "locator": element_role,
                        "strategy": LocatorStrategy.ROLE,
                        "reason": "role attribute",
                    })
                
                if element_text and len(element_text.strip()) < 100:
                    candidates.append({
                        "locator": element_text.strip(),
                        "strategy": LocatorStrategy.TEXT,
                        "reason": "text content",
                    })
                
                if placeholder:
                    candidates.append({
                        "locator": placeholder,
                        "strategy": LocatorStrategy.PLACEHOLDER,
                        "reason": "placeholder attribute",
                    })
                
                if name:
                    candidates.append({
                        "locator": name,
                        "strategy": LocatorStrategy.NAME,
                        "reason": "name attribute",
                    })
                
                if label:
                    candidates.append({
                        "locator": label.strip(),
                        "strategy": LocatorStrategy.LABEL,
                        "reason": "associated label",
                    })
                
                if element_class:
                    # Try CSS class-based selector
                    classes = element_class.split()
                    if classes:
                        css_selector = f"{tag_name}.{'.'.join(classes[:3])}"
                        candidates.append({
                            "locator": css_selector,
                            "strategy": LocatorStrategy.CSS,
                            "reason": "CSS class selector",
                        })
                
                # Try XPath based on position
                xpath = await element.evaluate("""el => {
                    const getPath = (node) => {
                        if (node.id) return '//' + node.tagName.toLowerCase() + '[@id="' + node.id + '"]';
                        if (node === document.body) return '/html/body';
                        const siblings = Array.from(node.parentNode.children).filter(c => c.tagName === node.tagName);
                        const index = siblings.indexOf(node) + 1;
                        return getPath(node.parentNode) + '/' + node.tagName.toLowerCase() + '[' + index + ']';
                    };
                    return getPath(el);
                }""")
                
                if xpath:
                    candidates.append({
                        "locator": xpath,
                        "strategy": LocatorStrategy.XPATH,
                        "reason": "XPath position",
                    })
            
        except Exception as e:
            logger.error("find_alternatives_error", error=str(e))
        
        if not candidates:
            # Element not found via original locator — scan page for similar elements
            candidates = await self._scan_similar_elements(page, original_locator)
        
        return candidates

    async def _scan_similar_elements(
        self,
        page: Page,
        original_locator: str,
    ) -> List[Dict[str, Any]]:
        """Scan interactive elements and find ones similar to the original locator."""
        import difflib
        candidates: List[Dict[str, Any]] = []
        try:
            elements = await page.evaluate("""() => {
                const nodes = Array.from(document.querySelectorAll(
                    'input, textarea, select, button, a[href], [role="button"], [contenteditable="true"]'
                ));
                return nodes.slice(0, 200).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    cls: el.getAttribute('class') || null,
                    testid: el.getAttribute('data-testid') || null,
                    placeholder: el.getAttribute('placeholder') || null,
                    name: el.getAttribute('name') || null,
                    type: el.getAttribute('type') || null,
                    text: (el.textContent || '').trim().slice(0, 120) || null,
                }));
            }""")

            orig = (original_locator or "").lower()
            tokens = [t for t in __import__('re').split(r"[^a-z0-9-]+", orig) if len(t) > 2]

            for el in elements:
                cls_val = el.get("cls")
                css_value = None
                if cls_val:
                    first_class = cls_val.strip().split()[0]
                    css_value = f".{first_class}"
                elif el.get("tag"):
                    css_value = el.get("tag")

                attr_map = {
                    LocatorStrategy.TEST_ID: el.get("testid"),
                    LocatorStrategy.ID: el.get("id"),
                    LocatorStrategy.NAME: el.get("name"),
                    LocatorStrategy.PLACEHOLDER: el.get("placeholder"),
                    LocatorStrategy.CSS: css_value,
                    LocatorStrategy.TEXT: el.get("text"),
                }
                best_ratio = 0.0
                best_strategy = None
                best_value = None
                for strategy, value in attr_map.items():
                    if not value:
                        continue
                    v = str(value).lower()
                    ratio = difflib.SequenceMatcher(None, orig, v).ratio()
                    # token containment boost
                    vt = [t for t in tokens if t and t in v]
                    if vt:
                        ratio = min(1.0, ratio + 0.15 * len(vt))
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_strategy = strategy
                        best_value = str(value)

                if best_value and best_ratio >= 0.55:
                    candidates.append({
                        "locator": best_value,
                        "strategy": best_strategy,
                        "reason": f"similar element on page ({el['tag']}, similarity {best_ratio:.0%})",
                        "similarity": best_ratio,
                    })
            candidates.sort(key=lambda c: c.get("similarity", 0), reverse=True)
            candidates = candidates[:5]
        except Exception as e:
            logger.error("scan_similar_elements_error", error=str(e))
        return candidates
    
    async def _locator_count(self, page: Page, locator: str, strategy: str) -> int:
        """Count matches for a candidate locator using Playwright Locator API."""
        s = str(getattr(strategy, "value", strategy))
        if s == "css":
            loc = page.locator(locator)
        elif s == "xpath":
            loc = page.locator(f"xpath={locator}")
        elif s == "text":
            loc = page.get_by_text(locator)
        elif s == "role":
            name, _, role = locator.partition("[")
            role = role.rstrip("]") if role else name
            loc = page.get_by_role(role, name=name if role else None)
        elif s == "testId":
            loc = page.locator(f"[data-testid='{locator}']")
        elif s == "id":
            loc = page.locator(f"#{locator}")
        elif s == "name":
            loc = page.locator(f"[name='{locator}']")
        elif s == "placeholder":
            loc = page.get_by_placeholder(locator)
        elif s == "label":
            loc = page.get_by_label(locator)
        else:
            loc = page.locator(locator)
        return await loc.count()

    async def _try_locator(self, page: Page, locator: str, strategy: str):
        """Try to find element with locator"""
        try:
            if strategy == "css":
                return await page.wait_for_selector(locator, timeout=1000)
            elif strategy == "xpath":
                return await page.wait_for_selector(f"xpath={locator}", timeout=1000)
            elif strategy == "text":
                return await page.wait_for_selector(f"text={locator}", timeout=1000)
            elif strategy == "role":
                return await page.wait_for_selector(f"role={locator}", timeout=1000)
            elif strategy == "testId":
                return await page.wait_for_selector(f"[data-testid={locator}]", timeout=1000)
            elif strategy == "id":
                return await page.wait_for_selector(f"#{locator}", timeout=1000)
            elif strategy == "name":
                return await page.wait_for_selector(f"[name={locator}]", timeout=1000)
            elif strategy == "placeholder":
                return await page.wait_for_selector(f"[placeholder={locator}]", timeout=1000)
            elif strategy == "label":
                return await page.wait_for_selector(f"label={locator}", timeout=1000)
        except Exception:
            return None
        return None
    
    async def _score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        page: Page,
    ) -> List[Dict[str, Any]]:
        """Score candidates based on uniqueness and stability"""
        scored = []
        
        for candidate in candidates:
            score = 0.5  # Base score
            reason = candidate["reason"]
            
            # Strategy preference scores
            strategy_scores = {
                LocatorStrategy.TEST_ID: 0.95,
                LocatorStrategy.ID: 0.9,
                LocatorStrategy.ROLE: 0.85,
                LocatorStrategy.LABEL: 0.8,
                LocatorStrategy.PLACEHOLDER: 0.75,
                LocatorStrategy.NAME: 0.7,
                LocatorStrategy.TEXT: 0.6,
                LocatorStrategy.CSS: 0.5,
                LocatorStrategy.XPATH: 0.4,
            }
            
            score = strategy_scores.get(candidate["strategy"], 0.5)

            # Verify candidate resolves uniquely
            try:
                count = await self._locator_count(page, candidate["locator"], candidate["strategy"])
                if count == 1:
                    score += 0.1  # Unique match bonus
                elif count > 1:
                    score -= 0.1 * min(count - 1, 3)  # Penalty for multiple matches
                else:
                    score = 0  # Not found
            except Exception:
                score = 0
            
            candidate["confidence"] = max(0, min(1, score * candidate.get("similarity", 1.0)))
            sim = candidate.get("similarity")
            sim_note = f", similarity {sim:.0%}" if sim else ""
            candidate["reasoning"] = f"{reason}{sim_note} (confidence: {candidate['confidence']:.0%})"
            scored.append(candidate)
        
        # Sort by confidence descending
        scored.sort(key=lambda x: x["confidence"], reverse=True)
        return scored
    
    async def apply_healing(
        self,
        candidate_id: uuid.UUID,
        approved: bool,
    ) -> bool:
        """Apply or reject a healing candidate"""
        async with async_session_maker() as db:
            candidate = await db.get(HealingCandidate, candidate_id)
            if not candidate:
                return False
            
            if approved:
                candidate.status = HealingStatus.APPROVED
                # TODO: Update step execution with healed locator
                # TODO: Store in locator memory
            else:
                candidate.status = HealingStatus.REJECTED
            
            candidate.reviewed_at = datetime.now(timezone.utc)
            candidate.reviewed_by = "user"
            
            await db.commit()
            return True


healer = Healer()