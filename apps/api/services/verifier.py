"""Verifier service for deterministic assertions"""
from dataclasses import dataclass
from typing import Any, Optional
from playwright.async_api import Page, Locator

logger = get_logger(__name__)


@dataclass
class AssertionResult:
    passed: bool
    message: str
    actual: Any = None
    expected: Any = None


class Verifier:
    """Deterministic assertion engine"""
    
    async def verify(
        self,
        page: Page,
        assertion: dict,
        locator: Optional[str] = None,
        strategy: str = "css",
    ) -> AssertionResult:
        """Verify an assertion"""
        assertion_type = assertion.get("type")
        expected = assertion.get("expected")
        operator = assertion.get("operator", "equals")
        
        try:
            if assertion_type == "visible":
                return await self._verify_visible(page, locator, strategy, expected)
            elif assertion_type == "hidden":
                return await self._verify_hidden(page, locator, strategy, expected)
            elif assertion_type == "enabled":
                return await self._verify_enabled(page, locator, strategy, expected)
            elif assertion_type == "disabled":
                return await self._verify_disabled(page, locator, strategy, expected)
            elif assertion_type == "text":
                return await self._verify_text(page, locator, strategy, expected, operator)
            elif assertion_type == "value":
                return await self._verify_value(page, locator, strategy, expected, operator)
            elif assertion_type == "count":
                return await self._verify_count(page, locator, strategy, expected, operator)
            elif assertion_type == "url":
                return await self._verify_url(page, expected, operator)
            elif assertion_type == "title":
                return await self._verify_title(page, expected, operator)
            else:
                return AssertionResult(
                    passed=False,
                    message=f"Unknown assertion type: {assertion_type}",
                )
        except Exception as e:
            logger.error("verification_error", assertion_type=assertion_type, error=str(e))
            return AssertionResult(
                passed=False,
                message=f"Verification error: {str(e)}",
            )
    
    async def _get_locator(self, page: Page, locator: Optional[str], strategy: str) -> Optional[Locator]:
        """Get Playwright locator from strategy"""
        if not locator:
            return None
        
        if strategy == "css":
            return page.locator(locator)
        elif strategy == "xpath":
            return page.locator(f"xpath={locator}")
        elif strategy == "text":
            return page.locator(f"text={locator}")
        elif strategy == "role":
            return page.locator(f"role={locator}")
        elif strategy == "testId":
            return page.locator(f"[data-testid={locator}]")
        elif strategy == "id":
            return page.locator(f"#{locator}")
        elif strategy == "name":
            return page.locator(f"[name={locator}]")
        elif strategy == "placeholder":
            return page.locator(f"[placeholder={locator}]")
        elif strategy == "label":
            return page.locator(f"label={locator}")
        else:
            return page.locator(locator)
    
    def _compare(self, actual: Any, expected: Any, operator: str) -> bool:
        """Compare values using operator"""
        if operator == "equals":
            return actual == expected
        elif operator == "contains":
            return str(expected) in str(actual)
        elif operator == "matches":
            import re
            return bool(re.match(str(expected), str(actual)))
        elif operator == "greaterThan":
            return float(actual) > float(expected)
        elif operator == "lessThan":
            return float(actual) < float(expected)
        return actual == expected
    
    async def _verify_visible(self, page: Page, locator: str, strategy: str, expected: bool) -> AssertionResult:
        element = await self._get_locator(page, locator, strategy)
        if not element:
            return AssertionResult(passed=False, message="No locator provided", actual=None, expected=expected)
        
        is_visible = await element.is_visible()
        passed = self._compare(is_visible, expected, "equals")
        return AssertionResult(
            passed=passed,
            message=f"Element visibility: expected {expected}, got {is_visible}",
            actual=is_visible,
            expected=expected,
        )
    
    async def _verify_hidden(self, page: Page, locator: str, strategy: str, expected: bool) -> AssertionResult:
        element = await self._get_locator(page, locator, strategy)
        if not element:
            return AssertionResult(passed=False, message="No locator provided", actual=None, expected=expected)
        
        is_hidden = await element.is_hidden()
        passed = self._compare(is_hidden, expected, "equals")
        return AssertionResult(
            passed=passed,
            message=f"Element hidden: expected {expected}, got {is_hidden}",
            actual=is_hidden,
            expected=expected,
        )
    
    async def _verify_enabled(self, page: Page, locator: str, strategy: str, expected: bool) -> AssertionResult:
        element = await self._get_locator(page, locator, strategy)
        if not element:
            return AssertionResult(passed=False, message="No locator provided", actual=None, expected=expected)
        
        is_enabled = await element.is_enabled()
        passed = self._compare(is_enabled, expected, "equals")
        return AssertionResult(
            passed=passed,
            message=f"Element enabled: expected {expected}, got {is_enabled}",
            actual=is_enabled,
            expected=expected,
        )
    
    async def _verify_disabled(self, page: Page, locator: str, strategy: str, expected: bool) -> AssertionResult:
        element = await self._get_locator(page, locator, strategy)
        if not element:
            return AssertionResult(passed=False, message="No locator provided", actual=None, expected=expected)
        
        is_disabled = await element.is_disabled()
        passed = self._compare(is_disabled, expected, "equals")
        return AssertionResult(
            passed=passed,
            message=f"Element disabled: expected {expected}, got {is_disabled}",
            actual=is_disabled,
            expected=expected,
        )
    
    async def _verify_text(
        self,
        page: Page,
        locator: str,
        strategy: str,
        expected: str,
        operator: str,
    ) -> AssertionResult:
        element = await self._get_locator(page, locator, strategy)
        if not element:
            return AssertionResult(passed=False, message="No locator provided", actual=None, expected=expected)
        
        actual_text = await element.text_content() or ""
        passed = self._compare(actual_text, expected, operator)
        return AssertionResult(
            passed=passed,
            message=f"Text {operator}: expected '{expected}', got '{actual_text}'",
            actual=actual_text,
            expected=expected,
        )
    
    async def _verify_value(
        self,
        page: Page,
        locator: str,
        strategy: str,
        expected: str,
        operator: str,
    ) -> AssertionResult:
        element = await self._get_locator(page, locator, strategy)
        if not element:
            return AssertionResult(passed=False, message="No locator provided", actual=None, expected=expected)
        
        actual_value = await element.input_value()
        passed = self._compare(actual_value, expected, operator)
        return AssertionResult(
            passed=passed,
            message=f"Value {operator}: expected '{expected}', got '{actual_value}'",
            actual=actual_value,
            expected=expected,
        )
    
    async def _verify_count(
        self,
        page: Page,
        locator: str,
        strategy: str,
        expected: int,
        operator: str,
    ) -> AssertionResult:
        element = await self._get_locator(page, locator, strategy)
        if not element:
            return AssertionResult(passed=False, message="No locator provided", actual=None, expected=expected)
        
        count = await element.count()
        passed = self._compare(count, expected, operator)
        return AssertionResult(
            passed=passed,
            message=f"Count {operator}: expected {expected}, got {count}",
            actual=count,
            expected=expected,
        )
    
    async def _verify_url(self, page: Page, expected: str, operator: str) -> AssertionResult:
        actual_url = page.url
        passed = self._compare(actual_url, expected, operator)
        return AssertionResult(
            passed=passed,
            message=f"URL {operator}: expected '{expected}', got '{actual_url}'",
            actual=actual_url,
            expected=expected,
        )
    
    async def _verify_title(self, page: Page, expected: str, operator: str) -> AssertionResult:
        actual_title = await page.title()
        passed = self._compare(actual_title, expected, operator)
        return AssertionResult(
            passed=passed,
            message=f"Title {operator}: expected '{expected}', got '{actual_title}'",
            actual=actual_title,
            expected=expected,
        )


verifier = Verifier()