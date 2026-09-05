import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Float, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
import enum

if TYPE_CHECKING:
    from models.run import TestRun, StepExecution


class VisualBaseline(Base):
    __tablename__ = "visual_baselines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    viewport_width: Mapped[int] = mapped_column(Integer, nullable=False)
    viewport_height: Mapped[int] = mapped_column(Integer, nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (Index("ix_visual_baselines_project_id", "project_id"),)


class VisualComparison(Base):
    __tablename__ = "visual_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    baseline_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visual_baselines.id", ondelete="CASCADE"), nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    step_execution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("step_executions.id", ondelete="CASCADE"), nullable=False)
    match: Mapped[bool] = mapped_column(nullable=False)
    difference_percent: Mapped[float] = mapped_column(Float, nullable=False)
    diff_image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    threshold: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        Index("ix_visual_comparisons_baseline_id", "baseline_id"),
        Index("ix_visual_comparisons_run_id", "run_id"),
    )


class AccessibilityImpact(str, enum.Enum):
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


class AccessibilityIssue(Base):
    __tablename__ = "accessibility_issues"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    step_execution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("step_executions.id", ondelete="CASCADE"), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    impact: Mapped[AccessibilityImpact] = mapped_column(SQLEnum(AccessibilityImpact, values_callable=lambda e: [m.value for m in e]), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    help: Mapped[str | None] = mapped_column(Text, nullable=True)
    html: Mapped[str | None] = mapped_column(Text, nullable=True)
    selector: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        Index("ix_accessibility_issues_run_id", "run_id"),
        Index("ix_accessibility_issues_impact", "impact"),
    )