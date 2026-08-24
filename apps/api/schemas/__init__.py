from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any


# Project Schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class ProjectResponse(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Environment Schemas
class EnvironmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    base_url: HttpUrl
    variables: Dict[str, str] = {}
    headers: Dict[str, str] = {}


class EnvironmentCreate(EnvironmentBase):
    pass


class EnvironmentUpdate(EnvironmentBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    base_url: Optional[HttpUrl] = None


class EnvironmentResponse(EnvironmentBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Test Step Schemas
class LocatorStrategy(str):
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ROLE = "role"
    TEST_ID = "testId"
    ID = "id"
    NAME = "name"
    PLACEHOLDER = "placeholder"
    LABEL = "label"


class AssertionSchema(BaseModel):
    type: str
    expected: Any
    operator: Optional[str] = None


class TestStepBase(BaseModel):
    order: int = Field(..., ge=0)
    action: str
    target: Optional[str] = None
    locator: Optional[str] = None
    locator_strategy: Optional[LocatorStrategy] = None
    value: Optional[str] = None
    options: Dict[str, Any] = {}
    assertion: Optional[AssertionSchema] = None
    description: Optional[str] = None
    continue_on_failure: bool = False


class TestStepCreate(TestStepBase):
    pass


class TestStepUpdate(BaseModel):
    order: Optional[int] = Field(None, ge=0)
    action: Optional[str] = None
    target: Optional[str] = None
    locator: Optional[str] = None
    locator_strategy: Optional[LocatorStrategy] = None
    value: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    assertion: Optional[AssertionSchema] = None
    description: Optional[str] = None
    continue_on_failure: Optional[bool] = None


class TestStepResponse(TestStepBase):
    id: UUID

    class Config:
        from_attributes = True


# Test Case Schemas
class TestCaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    steps: List[TestStepCreate] = []
    tags: List[str] = []


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    steps: Optional[List[TestStepCreate]] = None
    tags: Optional[List[str]] = None


class TestCaseResponse(TestCaseBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerateTestCaseRequest(BaseModel):
    intent: str = Field(..., min_length=10, max_length=5000)
    environment_id: Optional[UUID] = None
    context: Optional[str] = None


# Run Schemas
class RunStatus(str):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    HEALING = "healing"


class StepStatus(str):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    HEALING = "healing"
    HEALED = "healed"


class StepExecutionResponse(BaseModel):
    id: UUID
    run_id: UUID
    step_id: UUID
    order: int
    status: StepStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    dom_snapshot_path: Optional[str] = None
    console_logs: List[str] = []
    network_logs: List[Dict[str, Any]] = []
    trace_path: Optional[str] = None
    healed_locator: Optional[str] = None
    healing_candidate_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class TestRunBase(BaseModel):
    test_case_id: UUID
    environment_id: UUID
    triggered_by: Optional[str] = None
    commit_sha: Optional[str] = None
    branch: Optional[str] = None


class TestRunCreate(TestRunBase):
    pass


class TestRunResponse(TestRunBase):
    id: UUID
    project_id: UUID
    status: RunStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    created_at: datetime

    class Config:
        from_attributes = True


class TestRunDetailResponse(TestRunResponse):
    step_executions: List[StepExecutionResponse] = []

    class Config:
        from_attributes = True


# Healing Schemas
class HealingStatus(str):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class HealingCandidateResponse(BaseModel):
    id: UUID
    run_id: UUID
    step_execution_id: UUID
    original_locator: str
    original_strategy: LocatorStrategy
    suggested_locator: str
    suggested_strategy: LocatorStrategy
    confidence: float
    reasoning: str
    status: HealingStatus
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

    class Config:
        from_attributes = True


class ApproveHealingRequest(BaseModel):
    candidate_id: UUID
    approved: bool
    feedback: Optional[str] = None


# Design Intelligence Schemas
class VisualBaselineResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    viewport: Dict[str, int]
    image_path: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VisualComparisonResponse(BaseModel):
    baseline_id: UUID
    run_id: UUID
    step_execution_id: UUID
    match: bool
    difference_percent: float
    diff_image_path: Optional[str] = None
    threshold: float

    class Config:
        from_attributes = True


class AccessibilityIssueResponse(BaseModel):
    id: UUID
    run_id: UUID
    step_execution_id: UUID
    rule_id: str
    impact: str
    description: str
    help: Optional[str] = None
    html: Optional[str] = None
    selector: Optional[str] = None

    class Config:
        from_attributes = True


class DesignInsightResponse(BaseModel):
    run_id: UUID
    visual_comparisons: List[VisualComparisonResponse] = []
    accessibility_issues: List[AccessibilityIssueResponse] = []
    performance_metrics: Optional[Dict[str, float]] = None


# Memory Schemas
class MemoryType(str):
    LOCATOR = "locator"
    EPISODE = "episode"
    FAILURE_PATTERN = "failure_pattern"
    VISUAL_BASELINE = "visual_baseline"


class LocatorMemoryResponse(BaseModel):
    id: UUID
    project_id: UUID
    selector: str
    strategy: LocatorStrategy
    page_url: str
    element_role: Optional[str] = None
    element_text: Optional[str] = None
    success_count: int
    failure_count: int
    last_used_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class EpisodeMemoryResponse(BaseModel):
    id: UUID
    project_id: UUID
    intent: str
    steps: List[TestStepResponse]
    outcome: str
    run_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FailurePatternResponse(BaseModel):
    id: UUID
    project_id: UUID
    error_pattern: str
    step_action: str
    frequency: int
    suggested_fix: Optional[str] = None
    last_seen_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SearchMemoryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    types: Optional[List[MemoryType]] = None
    limit: int = Field(20, ge=1, le=100)


class SearchMemoryResponse(BaseModel):
    locators: List[LocatorMemoryResponse] = []
    episodes: List[EpisodeMemoryResponse] = []
    failure_patterns: List[FailurePatternResponse] = []
    visual_baselines: List[VisualBaselineResponse] = []


# SSE Event Schemas
class SSEEventType(str):
    RUN_STARTED = "run_started"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    HEALING_CANDIDATE = "healing_candidate"
    HEALING_APPROVED = "healing_approved"
    HEALING_REJECTED = "healing_rejected"
    RUN_COMPLETED = "run_completed"
    RUN_CANCELLED = "run_cancelled"
    LOG = "log"


class SSEEvent(BaseModel):
    type: SSEEventType
    run_id: UUID
    timestamp: datetime
    data: Dict[str, Any]


# Pagination
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int