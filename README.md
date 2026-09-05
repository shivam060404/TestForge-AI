# TestForge AI

TestForge AI is a full-stack prototype for autonomous, evidence-driven quality
assurance. It turns a natural-language test intent into a structured test case,
runs that case in a Playwright browser, captures evidence, verifies the result,
and helps a human review possible locator repairs. It also provides visual,
accessibility, and persistent-memory views so teams can investigate quality
signals in one place.

The project is designed around a simple rule: AI may assist with planning,
analysis, and recovery, but deterministic execution and verification remain the
source of truth.

## Who It Is For

TestForge AI is intended for:

- **QA automation engineers** who need less brittle selectors, run evidence, and
  faster failure diagnosis.
- **Frontend engineers** who want visual regression, accessibility signals, and
  browser-level functional checks.
- **Engineering managers and delivery leads** who need release confidence,
  run history, and quality metrics.
- **Product designers and design-system engineers** who want automated checks for
  visual drift and basic accessibility issues.
- **Researchers and platform engineers** exploring reliable, human-governed AI
  agents for software testing.

It is not a replacement for a complete CI/CD platform, a security scanner, a
mobile testing farm, or a production secrets manager.

## What It Does

The platform supports this workflow:

1. Create a project and target environment.
2. Describe a user journey in natural language or edit structured steps.
3. Generate a test case using deterministic patterns, project memory, and an
   optional Groq model.
4. Queue and execute the test in a Playwright browser worker.
5. Stream run status and inspect screenshots, DOM snapshots, logs, traces, and
   assertion results.
6. Classify failures and propose alternative locators or recovery actions.
7. Review and approve or reject healing candidates.
8. Compare screenshots with visual baselines and inspect design findings.
9. Persist verified locator, episode, and failure-pattern knowledge for later
   planning and diagnosis.

## Core Features

### Test authoring

- Project and environment management.
- Natural-language test intent input.
- Deterministic template planning when an LLM is unavailable.
- Optional structured-output LLM planning through a provider abstraction.
- Visual step editor with reordering, locators, assertions, and continue-on-failure
  controls.
- Guardrails that reject unsupported actions, unsafe output, empty intent, and
  malformed steps before execution.

### Browser execution and evidence

- Playwright-based Chromium execution.
- Queued background runs handled by a dedicated worker process.
- Step-by-step execution with live server-sent events (SSE).
- Screenshots, DOM snapshots, console logs, network logs, and traces.
- Run cancellation and retry flows.

### Deterministic verification

- Visibility and state assertions.
- Text and value assertions.
- URL and title assertions.
- Count assertions.
- Comparison operators including equals, contains, matches, greater-than, and
  less-than.

### Self-healing

- Candidate locators based on test IDs, IDs, roles, text, placeholders, labels,
  CSS, and XPath.
- Confidence, stability, uniqueness, semantic-match, and historical signals.
- Sandbox validation before a candidate is presented.
- Human approval and rejection workflow.
- Persisted locator and healing memory.

### Design intelligence

- Visual baseline creation and comparison.
- Pixel-level screenshot comparison using OpenCV.
- Difference image generation and run-level design insights.
- Basic accessibility and layout heuristics, including labels, contrast, focus,
  roles, overflow, broken images, and tap-target signals where supported by the
  current implementation.

### Memory and observability

- Locator memory with success and failure history.
- Episode memory for intent, steps, and outcomes.
- Failure-pattern memory with frequency and suggested fixes.
- Cross-type memory search.
- Structured logs for run, provider, model, prompt version, latency, token usage,
  and estimated cost.

## System Architecture

```mermaid
flowchart TD
    User[QA engineer or developer] --> Web[Next.js web application]
    Web -->|REST and SSE| API[FastAPI API]
    API --> DB[(PostgreSQL + pgvector image)]
    API --> Redis[(Redis)]
    API --> Minio[(MinIO artifact storage)]
    API --> Planner[Planner and AI runtime]
    Planner --> Guardrails[Prompt and output guardrails]
    Planner -->|optional| Groq[Groq provider]
    API --> Queue[Test run records]
    Worker[Background run worker] --> Queue
    Worker --> Orchestrator[Run orchestrator]
    Orchestrator --> Browser[Playwright Chromium]
    Browser --> Target[Target web application]
    Orchestrator --> Verifier[Deterministic verifier]
    Orchestrator --> Healer[Healing service]
    Orchestrator --> Design[Design intelligence]
    Orchestrator --> Minio
    Healer --> DB
    Design --> DB
    Memory[Memory service] --> DB
    Planner --> Memory
```

### Runtime boundaries

- **Web:** Next.js 14 App Router, TypeScript, Tailwind CSS, TanStack Query, and
  Zustand. It provides dashboards for projects, test cases, runs, healing,
  design intelligence, memory, and settings.
- **API:** FastAPI owns request validation, project resources, test-case
  resources, run state, SSE events, healing decisions, design insights, and
  memory queries.
- **Planner and AI runtime:** Deterministic planning and optional Groq calls are
  isolated behind a task-based provider router. Calls have bounded timeouts,
  retries, structured JSON output, prompt versions, and usage telemetry.
- **Worker:** `backend/workers/run_worker.py` polls pending runs and delegates
  execution to the orchestrator. The worker is separate from the API process.
- **Execution:** Playwright drives the browser. The verifier evaluates results
  deterministically; generated model output is never executed directly without
  validation.
- **Persistence:** PostgreSQL is required and accessed through async SQLAlchemy.
  Redis is used by the local platform for runtime coordination, and MinIO stores
  QA artifacts.

### Run lifecycle

```text
Create test case -> Queue run -> Worker claims pending run
    -> Planner/orchestrator prepares steps
    -> Playwright executes steps and captures evidence
    -> Verifier records assertions and outcome
    -> Healing/design services analyze failures and artifacts
    -> UI streams status and presents reviewable results
```

### AI safety model

1. Deterministic patterns and project memory are preferred before model use.
2. Intent length and structured step output are validated by guardrails.
3. Provider errors, timeouts, malformed output, and guardrail failures fall back
   to deterministic planning.
4. The model does not receive credentials as a normal part of the planning flow.
5. Healing remains a human approval workflow in the prototype.

Read the detailed design notes in [AI runtime architecture](docs/ai-runtime-architecture.md)
and [robust system design](docs/robust_system_design_architecture.md).

## Repository Layout

```text
.
├── backend/
│   ├── api/routes/       FastAPI route handlers
│   ├── core/             settings, database, logging, and AI runtime
│   ├── models/           SQLAlchemy persistence models
│   ├── services/         planning, execution, healing, design, and memory
│   ├── workers/          background run worker
│   ├── alembic/          database migrations
│   └── tests/            backend tests
├── frontend/
│   └── src/              Next.js pages, components, hooks, and API client
├── packages/shared/      shared TypeScript schemas and types
├── scripts/demo.py       end-to-end demonstration script
├── docs/                 product and architecture documentation
├── docker-compose.yml    local PostgreSQL, Redis, MinIO, API, web, and worker
└── .gitignore            generated files and local secrets
```

## Technology Stack

| Area | Technology |
| --- | --- |
| API | Python 3.11+, FastAPI, Pydantic v2 |
| Persistence | PostgreSQL 16 with pgvector image, SQLAlchemy 2, Alembic |
| Queue and coordination | Redis 7 |
| Artifact storage | MinIO with an S3-compatible API |
| Browser automation | Playwright and Chromium |
| AI provider | Optional Groq provider with structured JSON responses |
| Web application | Next.js 14, React 18, TypeScript |
| UI and data | Tailwind CSS, Radix UI, TanStack Query, Zustand, Recharts |
| Local orchestration | Docker Compose |

## Quick Start with Docker

### Prerequisites

- Docker Desktop with Docker Compose v2.
- At least 8 GB of memory available to Docker.
- Ports `3000`, `5432`, `6379`, `8000`, `9000`, and `9001` available.
- A Groq API key only if you want model-assisted test planning. Deterministic
  planning works without one.

### Start the platform

```bash
git clone https://github.com/shivam060404/TestForge-AI.git
cd TestForge-AI

# Optional: enable model-assisted planning for the API and worker.
export GROQ_API_KEY=your_key_here

docker compose up --build
```

The Compose stack runs migrations automatically for the API container and starts
the API, web application, worker, PostgreSQL, Redis, and MinIO.

| Service | URL |
| --- | --- |
| Web application | http://localhost:3000 |
| API root | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| MinIO API | http://localhost:9000 |
| MinIO console | http://localhost:9001 |

The default local MinIO credentials are `minioadmin` / `minioadmin`. Change them
before using the stack beyond local development.

### Run the demo

With the Compose stack running:

```bash
python3 scripts/demo.py
```

The demo checks API health, creates a project and environment, generates a
TodoMVC test, executes it, reviews a healing candidate if one is produced, and
queries design and memory endpoints. It is intended as a smoke test, not as a
production benchmark.

## Local Development

The services below still require PostgreSQL, Redis, and MinIO. Docker Compose is
the easiest way to run those dependencies.

### Backend API

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
alembic upgrade head
uvicorn main:app --reload --port 8000
```

Run the worker in a second terminal:

```bash
cd backend
source .venv/bin/activate
python -m workers.run_worker
```

`DATABASE_URL` must use PostgreSQL with the `asyncpg` driver. SQLite is
intentionally rejected so local behavior matches the Compose deployment.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend reads `NEXT_PUBLIC_API_URL` and defaults to
`http://localhost:8000` in the local Compose configuration.

### Shared package

```bash
cd packages/shared
npm install
npm run typecheck
```

## Configuration

The backend loads `backend/.env`. Start from `backend/.env.example`; never
commit a populated `.env` file or real credentials.

| Variable | Purpose | Local default |
| --- | --- | --- |
| `DATABASE_URL` | Async PostgreSQL connection | `postgresql+asyncpg://qa_user:qa_pass@localhost:5432/qa_agent` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `MINIO_ENDPOINT` | Artifact storage endpoint | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` |
| `MINIO_BUCKET` | Artifact bucket | `qa-artifacts` |
| `MINIO_USE_SSL` | Use TLS for MinIO | `false` |
| `SECRET_KEY` | Application secret | development placeholder |
| `ALLOWED_ORIGINS` | JSON list of CORS origins | `["http://localhost:3000"]` |
| `LOG_LEVEL` | Structured log level | `INFO` |
| `API_PREFIX` | API route prefix | `/api/v1` |
| `GROQ_API_KEY` | Optional Groq credential | empty |
| `GROQ_MODEL` | Groq model name | `openai/gpt-oss-120b` |
| `GROQ_TEMPERATURE` | Model sampling temperature | `0.1` |
| `GROQ_MAX_TOKENS` | Model response limit | `4096` |
| `LLM_TIMEOUT_SECONDS` | Provider timeout | `45` |
| `LLM_MAX_RETRIES` | Provider retry count | `2` |
| `AI_MAX_INTENT_LENGTH` | Maximum natural-language intent length | `5000` |
| `ARTIFACTS_DIR` | Local artifact directory setting | `./artifacts` |

## API Surface

The API is served under `/api/v1` by default. Interactive schemas are available
at `/docs`.

| Area | Main endpoints |
| --- | --- |
| Health | `GET /health`, `GET /` |
| Projects | CRUD under `/projects` |
| Environments | CRUD under `/projects/{project_id}/environments` and `/environments/{id}` |
| Test cases | CRUD under `/projects/{project_id}/test-cases`; natural-language generation at `/projects/{project_id}/test-cases/generate` |
| Runs | Create/list under projects, details at `/runs/{id}`, live events at `/runs/{id}/events`, cancel and retry actions |
| Healing | Candidates under `/runs/{run_id}/healing-candidates`; approve/reject under `/healing-candidates/{id}` |
| Design | Visual baselines under projects and design insights under `/runs/{run_id}/design-insights` |
| Memory | Locators, episodes, failure patterns, and search under `/projects/{project_id}/memory` |

Use the OpenAPI document generated by FastAPI as the authoritative contract for
request and response schemas.

## Database Migrations

```bash
cd backend
alembic upgrade head

# Create a migration after changing SQLAlchemy models.
alembic revision --autogenerate -m "describe the change"

# Roll back one migration during local development.
alembic downgrade -1
```

## Testing and Quality Checks

```bash
# Backend tests
cd backend
pytest

# Frontend type checking
cd frontend
npm run typecheck

# Frontend linting and production build
npm run lint
npm run build

# Shared package type checking
cd packages/shared
npm run typecheck
```

The current backend test suite includes AI guardrail checks. Add focused tests
for new route behavior, planner output, worker behavior, and healing decisions
alongside implementation changes.

## Security and Operational Notes

- Use non-default database, MinIO, and application secrets outside local
  development.
- Keep `.env`, API keys, credentials, browser artifacts, and generated reports
  out of Git. The repository `.gitignore` already excludes common local outputs.
- Restrict `ALLOWED_ORIGINS` to trusted web origins.
- Run browser jobs only against approved target environments in a controlled
  network. The prototype does not provide a complete target URL allowlist or
  production sandbox policy yet.
- Do not treat healing candidates as trusted code. Review and approve them before
  applying changes.
- Do not expose the development MinIO credentials or the unauthenticated API to
  the public internet.
- Review structured logs before enabling verbose logging in environments that
  process sensitive test data.
- PostgreSQL is mandatory; SQLite is unsupported by design.

## Current Limitations

The prototype does not yet provide:

- user authentication, SSO, or production-grade role-based access control;
- multi-tenant isolation and audit-grade authorization;
- distributed or multi-region browser execution;
- native mobile application testing;
- complete CI/CD marketplace integrations;
- full Figma synchronization;
- production secrets vault integration;
- a fully autonomous approval-free healing policy;
- a comprehensive accessibility engine equivalent to a dedicated accessibility
  platform.

## Roadmap

Near-term work is expected to focus on:

1. Authentication, authorization, project isolation, and audit trails.
2. Provider contract tests and a recorded prompt-regression suite.
3. Stronger URL allowlists and browser execution sandboxing.
4. Durable queue semantics, concurrency controls, and distributed workers.
5. CI/CD integrations and richer run analytics.
6. More complete accessibility, design-system, and visual-quality rules.
7. Production artifact retention, secret storage, and deployment automation.

The product requirements and architectural tradeoffs are documented in:

- [Product requirements](docs/PRD.md)
- [AI runtime architecture](docs/ai-runtime-architecture.md)
- [Robust system design](docs/robust_system_design_architecture.md)
- [Memory design](docs/memory.md)
- [Implementation phases](docs/Phases.txt)
- [Engineering rules](docs/Rules.txt)

## Contributing

1. Open an issue for a bug, design question, or feature proposal.
2. Keep changes scoped and consistent with the existing service boundaries.
3. Add or update focused tests for behavior changes.
4. Run the relevant backend, frontend, and shared-package checks.
5. Update this README or the deeper documentation when setup, API behavior, or
   architecture changes.
6. Never include secrets, generated dependencies, browser artifacts, or real
   customer data in a commit.

## License

MIT
