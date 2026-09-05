from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import configure_logging, get_logger
from core.database import init_db
from api.routes import health, projects, environments, test_cases, runs, healing, design, memory

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    logger.info("starting_up", version="0.1.0")
    await init_db()
    yield
    logger.info("shutting_down")


app = FastAPI(
    title="Autonomous QA Agent API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(environments.router, prefix=settings.api_prefix)
app.include_router(test_cases.router, prefix=settings.api_prefix)
app.include_router(runs.router, prefix=settings.api_prefix)
app.include_router(healing.router, prefix=settings.api_prefix)
app.include_router(design.router, prefix=settings.api_prefix)
app.include_router(memory.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {"name": "Autonomous QA Agent API", "version": "0.1.0", "status": "running"}