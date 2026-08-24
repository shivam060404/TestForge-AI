# Autonomous QA Agent

A full-stack prototype of an Autonomous QA Agent with Design Intelligence & Self-Healing Test Automation.

## Architecture

```
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js frontend
├── packages/
│   └── shared/       # Shared TypeScript/Python types & schemas
├── scripts/
│   └── demo.py       # End-to-end demo script
├── docker-compose.yml
└── README.md
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Playwright, PostgreSQL + pgvector, Redis, MinIO
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Zustand
- **Infrastructure**: Docker Compose for local development

## Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- 8GB+ RAM available for containers

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd autonomous-qa-agent

# Copy environment file
cp apps/api/.env.example apps/api/.env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

Services will be available at:
- **Frontend**: http://localhost:3000 (falls back to :3002 if :3000 is taken)
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### Local Development

#### Backend

```bash
cd apps/api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright
playwright install chromium

# Copy env file
cp .env.example .env

# Run migrations
alembic upgrade head

# Seed database (optional)
python scripts/seed.py

# Start development server
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd apps/web

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Shared Package

```bash
cd packages/shared
npm install
npm run typecheck
```

## Demo Flow

Run the automated demo script to see the complete end-to-end flow:

```bash
# Ensure services are running
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
# Then run demo
cd scripts
python3 demo.py
```

The demo will:
1. ✓ Check API health
2. ✓ Create project "E-commerce Demo"
3. ✓ Create environment "Staging" pointing to demo.playwright.dev/todomvc
4. ✓ Generate test case from natural language: "User adds a new todo item, marks it as complete, and filters to show only active todos"
5. ✓ Execute test in Playwright
6. ✓ Wait for completion
7. ✓ If failed, check healing candidates
8. ✓ Approve healing candidate
9. ✓ Retry test with healed locator
10. ✓ Get design insights (visual regression + accessibility)
11. ✓ Search memory for learned patterns

## Project Structure

### Backend (`apps/api/`)

```
apps/api/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── config.py          # Settings management (Pydantic Settings)
│   ├── database.py        # Database connection & session management
│   └── logging.py         # Structured logging (structlog)
├── models/                # SQLAlchemy models
│   ├── project.py         # Project model
│   ├── environment.py     # Environment model
│   ├── test_case.py       # TestCase & TestStep models
│   ├── run.py             # TestRun & StepExecution models
│   ├── healing.py         # HealingCandidate model
│   ├── design.py          # VisualBaseline, VisualComparison, AccessibilityIssue
│   └── memory.py          # LocatorMemory, EpisodeMemory, FailurePattern
├── schemas/               # Pydantic schemas (request/response)
├── api/
│   └── routes/            # API route handlers
│       ├── health.py
│       ├── projects.py
│       ├── environments.py
│       ├── test_cases.py
│       ├── runs.py
│       ├── healing.py
│       ├── design.py
│       └── memory.py
├── services/              # Business logic services
│   ├── orchestrator.py    # Test execution coordination
│   ├── playwright_worker.py # Playwright browser automation
│   ├── planner.py         # Natural language → test steps
│   ├── verifier.py        # Deterministic assertion engine
│   ├── healer.py          # Self-healing locator generation
│   ├── design_intelligence.py # Visual regression + accessibility
│   └── memory.py          # Persistent memory management
├── workers/
│   └── run_worker.py      # Background worker for run queue
├── alembic/               # Database migrations
│   ├── env.py
│   └── versions/
│       └── 001_initial_migration.py
├── scripts/
│   └── seed.py            # Database seeding
└── tests/                 # Unit & integration tests
```

### Frontend (`apps/web/`)

```
apps/web/
├── src/
│   ├── app/               # Next.js App Router pages
│   │   ├── layout.tsx     # Root layout with providers
│   │   ├── page.tsx       # Dashboard
│   │   ├── globals.css    # Tailwind + CSS variables
│   │   ├── providers.tsx  # React Query + Toast providers
│   │   ├── projects/      # Project management
│   │   │   ├── page.tsx   # Projects list
│   │   │   └── [id]/page.tsx # Project detail
│   │   ├── test-cases/    # Test case editor
│   │   │   └── [id]/page.tsx # Visual step editor
│   │   ├── runs/          # Test execution
│   │   │   ├── page.tsx   # Runs list
│   │   │   └── [id]/page.tsx # Live run console + report
│   │   ├── healing/       # Healing center
│   │   │   └── page.tsx   # Review/approve healing candidates
│   │   ├── design/        # Design intelligence
│   │   │   └── page.tsx   # Visual regression + accessibility
│   │   ├── memory/        # Memory browser
│   │   │   └── page.tsx   # Locators, episodes, failure patterns
│   │   └── settings/      # Settings page
│   ├── components/
│   │   ├── ui/            # shadcn/ui components (20+)
│   │   └── dashboard/     # Dashboard components
│   ├── hooks/             # Custom React hooks
│   │   ├── use-projects.ts
│   │   ├── use-environments.ts
│   │   ├── use-test-cases.ts
│   │   ├── use-runs.ts
│   │   ├── use-healing.ts
│   │   ├── use-design.ts
│   │   ├── use-memory.ts
│   │   └── use-toast.ts
│   ├── lib/
│   │   ├── api.ts         # Axios API client
│   │   └── utils.ts       # Utility functions
│   └── types/
│       └── index.ts       # TypeScript types (mirrors shared schemas)
├── public/                # Static assets
└── package.json
```

### Shared (`packages/shared/`)

```
packages/shared/
└── src/
    └── index.ts           # Zod schemas + TypeScript types
```

## API Endpoints

### Projects
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project
- `PATCH /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Environments
- `GET /api/v1/projects/{projectId}/environments` - List environments
- `POST /api/v1/projects/{projectId}/environments` - Create environment
- `GET /api/v1/environments/{id}` - Get environment
- `PATCH /api/v1/environments/{id}` - Update environment
- `DELETE /api/v1/environments/{id}` - Delete environment

### Test Cases
- `GET /api/v1/projects/{projectId}/test-cases` - List test cases
- `POST /api/v1/projects/{projectId}/test-cases` - Create test case
- `POST /api/v1/projects/{projectId}/test-cases/generate` - Generate from natural language
- `GET /api/v1/test-cases/{id}` - Get test case
- `PATCH /api/v1/test-cases/{id}` - Update test case
- `DELETE /api/v1/test-cases/{id}` - Delete test case

### Runs
- `GET /api/v1/projects/{projectId}/runs` - List runs
- `POST /api/v1/projects/{projectId}/runs` - Create run
- `GET /api/v1/runs/{id}` - Get run details
- `GET /api/v1/runs/{id}/events` - SSE stream for live updates
- `POST /api/v1/runs/{id}/cancel` - Cancel run
- `POST /api/v1/runs/{id}/retry` - Retry failed run

### Healing
- `GET /api/v1/runs/{runId}/healing-candidates` - List healing candidates
- `POST /api/v1/healing-candidates/{id}/approve` - Approve healing
- `POST /api/v1/healing-candidates/{id}/reject` - Reject healing

### Design Intelligence
- `GET /api/v1/projects/{projectId}/visual-baselines` - List baselines
- `POST /api/v1/projects/{projectId}/visual-baselines` - Create baseline
- `GET /api/v1/runs/{runId}/design-insights` - Get design insights
- `GET /api/v1/visual-baselines/{id}/compare` - Compare screenshot

### Memory
- `GET /api/v1/projects/{projectId}/memory/locators` - Locator memory
- `GET /api/v1/projects/{projectId}/memory/episodes` - Episode memory
- `GET /api/v1/projects/{projectId}/memory/failure-patterns` - Failure patterns
- `POST /api/v1/projects/{projectId}/memory/search` - Search memory

## Database Migrations

```bash
cd apps/api

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

```bash
# Backend tests
cd apps/api
pytest

# Frontend type checking
cd apps/web
npm run typecheck

# Frontend linting
npm run lint
```

## Environment Variables

### Backend (`apps/api/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://qa_user:qa_pass@localhost:5432/qa_agent` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `MINIO_ENDPOINT` | MinIO/S3 endpoint | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` |
| `MINIO_BUCKET` | Bucket for artifacts | `qa-artifacts` |
| `MINIO_USE_SSL` | Use SSL for MinIO | `false` |
| `SECRET_KEY` | JWT secret key | `dev-secret-key-change-in-production` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `["http://localhost:3000"]` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `API_PREFIX` | API route prefix | `/api/v1` |

### Frontend (`apps/web/.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000` |

## Key Features Implemented

### 1. Project & Environment Management
- Full CRUD for projects and environments
- Environment variables and headers support

### 2. Natural Language Test Generation
- Pattern-based intent recognition (login, checkout, search, etc.)
- Memory-aware generation using past successful episodes
- Extensible LLM integration point

### 3. Visual Test Step Editor
- Drag-and-drop step reordering
- Locator strategy selector (CSS, XPath, Text, Role, TestID, etc.)
- Assertion builder with multiple operators
- Continue-on-failure option

### 4. Playwright Test Execution
- Browser pool management
- Full evidence capture (screenshots, DOM snapshots, console logs, network logs, traces)
- Step-by-step execution with live SSE updates
- Structured error handling

### 5. Deterministic Assertion Engine
- 9 assertion types (visible, hidden, enabled, disabled, text, value, count, url, title)
- 5 comparison operators (equals, contains, matches, greaterThan, lessThan)
- JSON-schema validated outputs

### 6. Self-Healing Locators
- Alternative locator generation (TestID, ID, Role, Text, Placeholder, Label, CSS, XPath)
- Confidence scoring based on strategy stability and uniqueness
- Approval workflow with feedback
- Memory persistence for learned healings

### 7. Design Intelligence
- Visual baseline management
- Pixel-level screenshot comparison with OpenCV
- Configurable difference threshold
- Accessibility issue detection (simulated axe-core integration)
- Diff image generation

### 8. Persistent Memory
- Locator memory (success/failure tracking per selector)
- Episode memory (intent → steps → outcome)
- Failure pattern recognition (error pattern → frequency → suggested fix)
- Cross-type search with relevance scoring

### 9. Modern UI
- Dashboard with metrics and quick actions
- Live run console with SSE streaming
- Expandable step details with artifacts
- Healing center with diff view
- Design insights with visual diffs
- Memory browser with expandable rows
- Full settings panel

## Contributing

1. Follow the implementation order in the specification
2. Maintain type safety across backend and frontend (shared schemas)
3. Use structured logging
4. Write tests for new features
5. Update documentation

## License

MIT