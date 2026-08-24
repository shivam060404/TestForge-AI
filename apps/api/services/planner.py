"""Planner service for natural language to test steps conversion"""
import json
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.logging import get_logger
from services.memory import memory_service

logger = get_logger(__name__)


@dataclass
class PlannedStep:
    order: int
    action: str
    target: Optional[str] = None
    locator: Optional[str] = None
    locator_strategy: Optional[str] = None
    value: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    assertion: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    continue_on_failure: bool = False


class Planner:
    """Converts natural language intent to structured test steps"""
    
    def __init__(self):
        self.system_prompt = """You are an expert QA engineer that converts natural language test descriptions into structured test steps for Playwright automation.

Rules:
1. Output ONLY valid JSON matching the exact schema provided
2. Use deterministic locators: prefer data-testid > id > role > CSS > XPath
3. Each step must have an action from: goto, click, fill, select, hover, wait, assert, screenshot, scroll, press, check, uncheck
4. Include assertions for verification steps
5. Keep steps atomic and independent
6. Use semantic locators (role, text, testId) over brittle CSS/XPath
7. Include meaningful descriptions for each step

Schema for each step:
{
  "order": integer,
  "action": "goto|click|fill|select|hover|wait|assert|screenshot|scroll|press|check|uncheck",
  "target": "optional URL path for goto",
  "locator": "locator string",
  "locator_strategy": "css|xpath|text|role|testId|id|name|placeholder|label",
  "value": "input value for fill/select/press",
  "options": {},
  "assertion": {"type": "visible|hidden|enabled|disabled|text|value|count|url|title", "expected": value, "operator": "equals|contains|matches|greaterThan|lessThan"},
  "description": "human readable description",
  "continue_on_failure": boolean
}"""

        # Common patterns for pattern matching
        self.patterns = {
            "login": [
                PlannedStep(0, "goto", target="/login", description="Navigate to login page"),
                PlannedStep(1, "fill", locator="[data-testid=email]", locator_strategy="testId", value="{email}", description="Enter email"),
                PlannedStep(2, "fill", locator="[data-testid=password]", locator_strategy="testId", value="{password}", description="Enter password"),
                PlannedStep(3, "click", locator="[data-testid=login-button]", locator_strategy="testId", description="Click login button"),
                PlannedStep(4, "assert", locator="[data-testid=user-menu]", locator_strategy="testId", assertion={"type": "visible", "expected": True}, description="Verify login success"),
            ],
            "add_to_cart": [
                PlannedStep(0, "goto", target="/products", description="Navigate to products page"),
                PlannedStep(1, "click", locator="[data-testid=product-{product}]", locator_strategy="testId", description="Select product"),
                PlannedStep(2, "click", locator="[data-testid=add-to-cart]", locator_strategy="testId", description="Add to cart"),
                PlannedStep(3, "assert", locator="[data-testid=cart-count]", locator_strategy="testId", assertion={"type": "text", "expected": "1", "operator": "contains"}, description="Verify cart updated"),
            ],
            "checkout": [
                PlannedStep(0, "goto", target="/cart", description="Navigate to cart"),
                PlannedStep(1, "click", locator="[data-testid=checkout]", locator_strategy="testId", description="Start checkout"),
                PlannedStep(2, "fill", locator="[data-testid=shipping-name]", locator_strategy="testId", value="{name}", description="Enter shipping name"),
                PlannedStep(3, "fill", locator="[data-testid=shipping-address]", locator_strategy="testId", value="{address}", description="Enter address"),
                PlannedStep(4, "fill", locator="[data-testid=shipping-email]", locator_strategy="testId", value="{email}", description="Enter email"),
                PlannedStep(5, "click", locator="[data-testid=continue-payment]", locator_strategy="testId", description="Continue to payment"),
                PlannedStep(6, "fill", locator="[data-testid=card-number]", locator_strategy="testId", value="{card}", description="Enter card number"),
                PlannedStep(7, "fill", locator="[data-testid=card-expiry]", locator_strategy="testId", value="{expiry}", description="Enter expiry"),
                PlannedStep(8, "fill", locator="[data-testid=card-cvc]", locator_strategy="testId", value="{cvc}", description="Enter CVC"),
                PlannedStep(9, "click", locator="[data-testid=pay-button]", locator_strategy="testId", description="Complete payment"),
                PlannedStep(10, "assert", locator="[data-testid=order-confirmation]", locator_strategy="testId", assertion={"type": "visible", "expected": True}, description="Verify order confirmation"),
            ],
            "search": [
                PlannedStep(0, "goto", target="/", description="Navigate to home page"),
                PlannedStep(1, "fill", locator="[data-testid=search-input]", locator_strategy="testId", value="{query}", description="Enter search query"),
                PlannedStep(2, "press", locator="[data-testid=search-input]", locator_strategy="testId", value="Enter", description="Submit search"),
                PlannedStep(3, "assert", locator="[data-testid=search-results]", locator_strategy="testId", assertion={"type": "visible", "expected": True}, description="Verify results displayed"),
            ],
        }
    
    async def generate_steps(
        self,
        intent: str,
        project_id: uuid.UUID,
        environment_id: Optional[uuid.UUID] = None,
        context: Optional[str] = None,
    ) -> List[PlannedStep]:
        """Generate test steps from natural language intent"""
        
        # Try pattern matching first
        steps = self._match_patterns(intent)
        if steps:
            logger.info("steps_generated_from_pattern", intent=intent[:50], step_count=len(steps))
            return steps
        
        # Try to find similar episodes from memory
        episodes = await memory_service.get_episodes_for_intent(project_id, intent)
        if episodes:
            # Use the most recent successful episode as template
            episode = episodes[0]
            steps = [PlannedStep(**step) for step in episode.steps]
            logger.info("steps_generated_from_memory", intent=intent[:50], step_count=len(steps))
            return steps
        
        # Fallback to LLM-based generation (placeholder for now)
        steps = await self._llm_generate(intent, context)
        logger.info("steps_generated_from_llm", intent=intent[:50], step_count=len(steps))
        return steps
    
    def _match_patterns(self, intent: str) -> Optional[List[PlannedStep]]:
        """Match intent against known patterns"""
        intent_lower = intent.lower()
        
        if any(keyword in intent_lower for keyword in ["login", "sign in", "log in"]):
            return self.patterns["login"]
        
        if any(keyword in intent_lower for keyword in ["add to cart", "add item", "buy product"]):
            return self.patterns["add_to_cart"]
        
        if any(keyword in intent_lower for keyword in ["checkout", "purchase", "complete order", "place order"]):
            return self.patterns["checkout"]
        
        if any(keyword in intent_lower for keyword in ["search", "find", "look for"]):
            return self.patterns["search"]
        
        return None
    
    async def _llm_generate(
        self,
        intent: str,
        context: Optional[str] = None,
    ) -> List[PlannedStep]:
        """Generate steps using LLM (placeholder implementation)"""
        # In production, this would call an LLM API
        # For now, return a generic template
        
        # This is a simplified template - real implementation would use LLM
        steps = [
            PlannedStep(
                order=0,
                action="goto",
                target="/",
                description="Navigate to application",
            ),
            PlannedStep(
                order=1,
                action="wait",
                value="2",
                description="Wait for page load",
            ),
        ]
        
        # Parse intent for common actions
        intent_lower = intent.lower()
        
        if "click" in intent_lower:
            steps.append(PlannedStep(
                order=len(steps),
                action="click",
                locator="button:has-text('Submit')",
                locator_strategy="css",
                description="Click submit button",
            ))
        
        if "fill" in intent_lower or "enter" in intent_lower or "type" in intent_lower:
            steps.append(PlannedStep(
                order=len(steps),
                action="fill",
                locator="input[type='text']",
                locator_strategy="css",
                value="test value",
                description="Fill input field",
            ))
        
        if "verify" in intent_lower or "check" in intent_lower or "assert" in intent_lower:
            steps.append(PlannedStep(
                order=len(steps),
                action="assert",
                locator="body",
                locator_strategy="css",
                assertion={"type": "visible", "expected": True},
                description="Verify page loaded",
            ))
        
        return steps
    
    def validate_steps(self, steps: List[PlannedStep]) -> List[str]:
        """Validate generated steps"""
        errors = []
        
        for i, step in enumerate(steps):
            if step.action not in ("goto", "click", "fill", "select", "hover", "wait", "assert", "screenshot", "scroll", "press", "check", "uncheck"):
                errors.append(f"Step {i}: Invalid action '{step.action}'")
            
            if step.action == "goto" and not step.target:
                errors.append(f"Step {i}: goto requires target")
            
            if step.action in ("click", "fill", "select", "hover", "check", "uncheck", "press") and not step.locator:
                errors.append(f"Step {i}: {step.action} requires locator")
            
            if step.action == "assert" and not step.assertion:
                errors.append(f"Step {i}: assert requires assertion")
        
        return errors


planner = Planner()