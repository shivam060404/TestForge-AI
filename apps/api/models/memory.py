import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
import enum

if TYPE_CHECKING:
    from models.project import Project


class LocatorStrategy(str, enum.Enum):
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ROLE = "role"
    TEST_ID = "testId"
    ID = "id"
    NAME = "name"
    PLACEHOLDER = "placeholder"
    LABEL = "label"


class LocatorMemory(Base):
    __tablename__ = "locator_memory"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    selector: Mapped[str] = mapped_column(Text, nullable=False)
    strategy: Mapped[LocatorStrategy] = mapped_column(SQLEnum(LocatorStrategy), nullable=False)
    page_url: Mapped[str] = mapped_column(Text, nullable=False)
    element_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    element_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        Index("ix_locator_memory_project_id", "project_id"),
        Index("ix_locator_memory_selector", "project_id", "selector"),
    )


class EpisodeOutcome(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class EpisodeMemory(Base):
    __tablename__ = "episode_memory"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    intent: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    outcome: Mapped[EpisodeOutcome] = mapped_column(SQLEnum(EpisodeOutcome), nullable=False)
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("test_runs.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (Index("ix_episode_memory_project_id", "project_id"),)


class FailurePattern(Base):
    __tablename__ = "failure_patterns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    error_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    step_action: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (Index("ix_failure_patterns_project_id", "project_id"),)