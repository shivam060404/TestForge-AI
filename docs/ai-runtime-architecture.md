# AI Runtime Architecture

The prototype keeps deterministic QA execution as the source of truth and isolates
model-assisted behavior behind explicit runtime boundaries.

## Runtime boundaries

- **LLM abstraction and routing**: `backend/core/ai/runtime.py` exposes a provider
  protocol and task-based router. Providers have bounded timeouts, exponential
  retries, structured usage accounting, and model/provider metadata.
- **Prompt management**: `backend/core/ai/prompts.py` stores named, versioned
  templates. Every model result records the prompt version in structured logs.
- **Grounding**: planner context is passed as a clearly delimited grounded context
  block. Deterministic patterns and project memory are preferred before the LLM.
- **Guardrails**: `backend/core/ai/guardrails.py` validates intent size and the
  complete structured step contract before model output can become a test case.
  Unsupported actions and missing locators/assertions are rejected.
- **Failure isolation**: provider errors, timeouts, malformed output, and guardrail
  violations degrade to a deterministic template planner. They never bypass
  validation or execute model-generated commands directly.
- **Observability and cost**: every provider call logs provider, model, prompt
  version, latency, token usage, and estimated cost. Cost rates are configurable
  rather than hard-coded.
- **Human approval**: healing remains an explicit approval workflow; generated
  tests are persisted for review before execution.

## PostgreSQL contract

PostgreSQL is mandatory. The backend validates `postgresql+asyncpg://` at settings
load time and again at database initialization. Local Compose, Alembic, CI, and
the async SQLAlchemy pool all use PostgreSQL. SQLite is intentionally unsupported
so development behavior matches production semantics.

## Evaluation and delivery

Focused guardrail tests run in CI alongside Python compilation, frontend type
checking, and the optimized Next.js build. The next production increment should
add a recorded prompt regression set and provider contract tests using a mocked
LLM transport before changing prompt versions.
