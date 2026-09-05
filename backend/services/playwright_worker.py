"""Playwright worker for browser automation"""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class PlaywrightWorker:
    """Manages Playwright browser instances and executes test steps"""
    
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.tracing = False
        self.artifacts_dir = Path(settings.artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self, headless: bool = True) -> None:
        """Initialize browser and context"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
            ],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(self.artifacts_dir / "videos"),
        )
        
        # Enable tracing
        await self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.tracing = True
        
        self.page = await self.context.new_page()
        
        # Set up console log capture
        self._console_logs: List[str] = []
        self._network_logs: List[Dict[str, Any]] = []
        
        self.page.on("console", lambda msg: self._console_logs.append(f"[{msg.type}] {msg.text}"))
        self.page.on("request", lambda req: self._network_logs.append({
            "url": req.url,
            "method": req.method,
            "headers": dict(req.headers),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))
        self.page.on("response", lambda resp: self._network_logs.append({
            "url": resp.url,
            "status": resp.status,
            "headers": dict(resp.headers),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))
        
        logger.info("playwright_initialized")
    
    async def execute_step(
        self,
        action: str,
        url: str,
        locator: Optional[str],
        strategy: str,
        value: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a single test step"""
        if not self.page:
            raise RuntimeError("Playwright not initialized")
        
        options = options or {}
        timeout = options.get("timeout", 30000)
        
        try:
            if action == "goto":
                await self.page.goto(url, wait_until="networkidle", timeout=timeout)
                return {"success": True, "url": self.page.url}
            
            elif action in ("click", "hover", "check", "uncheck"):
                element = await self._find_element(locator, strategy, timeout)
                if action == "click":
                    await element.click(**options)
                elif action == "hover":
                    await element.hover()
                elif action == "check":
                    await element.check()
                elif action == "uncheck":
                    await element.uncheck()
                return {"success": True}
            
            elif action == "fill":
                element = await self._find_element(locator, strategy, timeout)
                await element.fill(value or "", **options)
                return {"success": True}
            
            elif action == "select":
                element = await self._find_element(locator, strategy, timeout)
                await element.select_option(value or "", **options)
                return {"success": True}
            
            elif action == "press":
                element = await self._find_element(locator, strategy, timeout)
                await element.press(value or "Enter", **options)
                return {"success": True}
            
            elif action == "wait":
                if locator:
                    await self._find_element(locator, strategy, timeout)
                else:
                    await asyncio.sleep(float(value or "1"))
                return {"success": True}
            
            elif action == "scroll":
                if locator:
                    element = await self._find_element(locator, strategy, timeout)
                    await element.scroll_into_view_if_needed()
                else:
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                return {"success": True}
            
            elif action == "screenshot":
                path = await self.capture_screenshot(uuid.uuid4(), uuid.uuid4())
                return {"success": True, "screenshot_path": path}
            
            elif action == "assert":
                # Assertions are handled by the verifier service
                return {"success": True}
            
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error("step_execution_failed", action=action, error=str(e))
            raise
    
    async def _find_element(self, locator: str, strategy: str, timeout: int) -> Any:
        """Find element using specified strategy"""
        if not self.page:
            raise RuntimeError("Page not initialized")
        
        if strategy == "css":
            return await self.page.wait_for_selector(locator, timeout=timeout)
        elif strategy == "xpath":
            return await self.page.wait_for_selector(f"xpath={locator}", timeout=timeout)
        elif strategy == "text":
            return await self.page.wait_for_selector(f"text={locator}", timeout=timeout)
        elif strategy == "role":
            return await self.page.wait_for_selector(f"role={locator}", timeout=timeout)
        elif strategy == "testId":
            return await self.page.wait_for_selector(f"[data-testid={locator}]", timeout=timeout)
        elif strategy == "id":
            return await self.page.wait_for_selector(f"#{locator}", timeout=timeout)
        elif strategy == "name":
            return await self.page.wait_for_selector(f"[name={locator}]", timeout=timeout)
        elif strategy == "placeholder":
            return await self.page.wait_for_selector(f"[placeholder={locator}]", timeout=timeout)
        elif strategy == "label":
            return await self.page.wait_for_selector(f"label={locator}", timeout=timeout)
        else:
            raise ValueError(f"Unknown locator strategy: {strategy}")
    
    async def capture_screenshot(self, run_id: uuid.UUID, step_execution_id: uuid.UUID) -> str:
        """Capture screenshot and save to artifacts"""
        if not self.page:
            return ""
        
        filename = f"{run_id}_{step_execution_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.png"
        path = self.artifacts_dir / "screenshots" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        
        await self.page.screenshot(path=str(path), full_page=True)
        logger.debug("screenshot_captured", path=str(path))
        return str(path)
    
    async def capture_dom_snapshot(self, run_id: uuid.UUID, step_execution_id: uuid.UUID) -> str:
        """Capture DOM snapshot"""
        if not self.page:
            return ""
        
        filename = f"{run_id}_{step_execution_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.html"
        path = self.artifacts_dir / "dom_snapshots" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        
        html = await self.page.content()
        path.write_text(html)
        logger.debug("dom_snapshot_captured", path=str(path))
        return str(path)
    
    async def get_console_logs(self) -> List[str]:
        """Get captured console logs"""
        logs = self._console_logs.copy()
        self._console_logs.clear()
        return logs
    
    async def get_network_logs(self) -> List[Dict[str, Any]]:
        """Get captured network logs"""
        logs = self._network_logs.copy()
        self._network_logs.clear()
        return logs
    
    async def stop_tracing(self, run_id: uuid.UUID, step_execution_id: uuid.UUID) -> str:
        """Stop tracing and save trace file"""
        if not self.context or not self.tracing:
            return ""
        
        filename = f"{run_id}_{step_execution_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
        path = self.artifacts_dir / "traces" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        
        await self.context.tracing.stop(path=str(path))
        self.tracing = False
        
        # Restart tracing for next step
        await self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.tracing = True
        
        logger.debug("trace_captured", path=str(path))
        return str(path)
    
    async def cleanup(self) -> None:
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        logger.info("playwright_cleanup")


# Global worker instance
worker = PlaywrightWorker()