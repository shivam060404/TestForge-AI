import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
import enum

if TYPE_CHECKING:
    from models.project import Project
    from models.test_case import TestCase
    from models.environment import Environment
    from models.healing import HealingCandidate


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    HEALING = "healing"


class StepStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    HEALING = "healing"
    HEALED = "healed"


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    test_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    environment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("environments.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[RunStatus] = mapped_column(SQLEnum(RunStatus, values_callable=lambda e: [m.value for m in e]), default=RunStatus.PENDING, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    triggered_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(100), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="runs")
    test_case: Mapped["TestCase"] = relationship(back_populates="runs")
    environment: Mapped["Environment"] = relationship(back_populates="runs")
    step_executions: Mapped[list["StepExecution"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    healing_candidates: Mapped[list["HealingCandidate"]] = relationship(back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_test_runs_project_id", "project_id"),
        Index("ix_test_runs_status", "status"),
        Index("ix_test_runs_created_at", "created_at"),
    )


class StepExecution(Base):
    __tablename__ = "step_executions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    # Steps are stored as JSON on test_cases; step_id references the logical step (no FK)
    step_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StepStatus] = mapped_column(SQLEnum(StepStatus, values_callable=lambda e: [m.value for m in e]), default=StepStatus.PENDING, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    dom_snapshot_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    console_logs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    network_logs: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    trace_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    healed_locator: Mapped[str | None] = mapped_column(Text, nullable=True)
    healing_candidate_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("healing_candidates.id", ondelete="SET NULL"), nullable=True)

    run: Mapped["TestRun"] = relationship(back_populates="step_executions")

    __table_args__ = (
        Index("ix_step_executions_run_id", "run_id"),
        Index("ix_step_executions_step_id", "step_id"),
        Index("ix_step_executions_order", "run_id", "order"),
    )