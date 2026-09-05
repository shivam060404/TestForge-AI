import asyncio
import time
from dataclasses import dataclass
from typing import Any, Protocol

from groq import AsyncGroq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class LLMResult:
    content: str
    provider: str
    model: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    latency_ms: int


class LLMProvider(Protocol):
    async def complete(self, *, system: str, user: str, model: str, prompt_version: str) -> LLMResult: ...


class GroqProvider:
    name = "groq"

    def __init__(self, client: AsyncGroq):
        self.client = client

    async def complete(self, *, system: str, user: str, model: str, prompt_version: str) -> LLMResult:
        started = time.perf_counter()

        @retry(
            retry=retry_if_exception_type(Exception),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
            stop=stop_after_attempt(settings.llm_max_retries + 1),
            reraise=True,
        )
        async def request() -> Any:
            return await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    temperature=settings.groq_temperature,
                    max_tokens=settings.groq_max_tokens,
                    response_format={"type": "json_object"},
                ),
                timeout=settings.llm_timeout_seconds,
            )

        response = await request()
        usage = response.usage
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0
        cost = (
            input_tokens / 1000 * settings.llm_cost_per_1k_input_tokens
            + output_tokens / 1000 * settings.llm_cost_per_1k_output_tokens
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "llm_call_completed", provider=self.name, model=model,
            prompt_version=prompt_version, input_tokens=input_tokens,
            output_tokens=output_tokens, estimated_cost_usd=cost, latency_ms=latency_ms,
        )
        return LLMResult(
            content=response.choices[0].message.content or "",
            provider=self.name, model=model, prompt_version=prompt_version,
            input_tokens=input_tokens, output_tokens=output_tokens,
            estimated_cost_usd=cost, latency_ms=latency_ms,
        )


class LLMRouter:
    def __init__(self) -> None:
        self._groq = GroqProvider(AsyncGroq(api_key=settings.groq_api_key)) if settings.groq_api_key else None

    async def complete(self, *, task: str, system: str, user: str, prompt_version: str) -> LLMResult | None:
        if task != "test_planning":
            raise ValueError(f"Unsupported LLM task: {task}")
        if not self._groq:
            logger.warning("llm_provider_unavailable", task=task)
            return None
        return await self._groq.complete(
            system=system, user=user, model=settings.groq_model, prompt_version=prompt_version,
        )


llm_router = LLMRouter()
