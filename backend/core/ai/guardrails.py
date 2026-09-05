import json
from typing import Any

from core.config import settings

ALLOWED_ACTIONS = {
    "goto", "click", "fill", "select", "hover", "wait", "assert",
    "screenshot", "scroll", "press", "check", "uncheck",
}


class GuardrailViolation(ValueError):
    """Raised when model output cannot be safely executed."""


def validate_intent(intent: str) -> str:
    value = intent.strip()
    if not value:
        raise GuardrailViolation("Test intent cannot be empty")
    if len(value) > settings.ai_max_intent_length:
        raise GuardrailViolation("Test intent exceeds the configured limit")
    return value


def parse_and_validate_steps(payload: str | dict[str, Any]) -> list[dict[str, Any]]:
    data = json.loads(payload) if isinstance(payload, str) else payload
    steps = data if isinstance(data, list) else data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise GuardrailViolation("Model response must contain a non-empty steps array")
    validated: list[dict[str, Any]] = []
    for index, raw_step in enumerate(steps):
        if not isinstance(raw_step, dict):
            raise GuardrailViolation(f"Step {index} must be an object")
        step = dict(raw_step)
        action = step.get("action")
        if action not in ALLOWED_ACTIONS:
            raise GuardrailViolation(f"Step {index} has unsupported action")
        if action == "goto" and not step.get("target"):
            raise GuardrailViolation(f"Step {index} goto requires target")
        if action in {"click", "fill", "select", "hover", "check", "uncheck", "press"} and not step.get("locator"):
            raise GuardrailViolation(f"Step {index} requires a locator")
        if action == "assert" and not isinstance(step.get("assertion"), dict):
            raise GuardrailViolation(f"Step {index} assert requires assertion metadata")
        step["order"] = index
        validated.append(step)
    return validated
