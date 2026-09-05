from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    system: str


TEST_PLANNER_PROMPT = PromptTemplate(
    name="test-planner",
    version="v1",
    system="""You are an expert QA engineer converting a test intent into safe,
deterministic Playwright steps. Return only JSON with a `steps` array.
Prefer data-testid, id, role, label, and text locators over brittle XPath.
Never invent credentials, secrets, destructive actions, or external side effects.
Allowed actions: goto, click, fill, select, hover, wait, assert, screenshot,
scroll, press, check, uncheck.""",
)


def render_planner_user_prompt(intent: str, context: str | None) -> str:
    context_block = f"\nGrounded application context:\n{context}" if context else ""
    return (
        "Convert this intent into executable test steps.\n"
        f"Intent:\n{intent}{context_block}\n"
        'Return {"steps":[{"order":0,"action":"...","target":null,'
        '"locator":null,"locator_strategy":null,"value":null,"options":{},'
        '"assertion":null,"description":"...","continue_on_failure":false}]}'
    )
