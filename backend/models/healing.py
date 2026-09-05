import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, Float, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
import enum

if TYPE_CHECKING:
    from models.run import TestRun, StepExecution


class HealingStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class HealingCandidate(Base):
    __tablename__ = "healing_candidates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    step_execution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("step_executions.id", ondelete="CASCADE"), nullable=False)
    original_locator: Mapped[str] = mapped_column(Text, nullable=False)
    original_strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    suggested_locator: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[HealingStatus] = mapped_column(SQLEnum(HealingStatus, values_callable=lambda e: [m.value for m in e]), default=HealingStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    run: Mapped["TestRun"] = relationship(back_populates="healing_candidates")
    step_execution: Mapped["StepExecution"] = relationship(
        foreign_keys=[step_execution_id]
    )

    __table_args__ = (
        Index("ix_healing_candidates_run_id", "run_id"),
        Index("ix_healing_candidates_status", "status"),
    )