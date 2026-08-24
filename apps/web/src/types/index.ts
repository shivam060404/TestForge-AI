// Base types
export type UUID = string;
export type Timestamp = string;

// Pagination
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Project
export interface Project {
  id: UUID;
  name: string;
  description?: string;
  created_at: Timestamp;
  updated_at: Timestamp;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
}

// Environment
export interface Environment {
  id: UUID;
  project_id: UUID;
  name: string;
  base_url: string;
  variables: Record<string, string>;
  headers: Record<string, string>;
  created_at: Timestamp;
  updated_at: Timestamp;
}

export interface CreateEnvironmentRequest {
  name: string;
  base_url: string;
  variables?: Record<string, string>;
  headers?: Record<string, string>;
}

export interface UpdateEnvironmentRequest {
  name?: string;
  base_url?: string;
  variables?: Record<string, string>;
  headers?: Record<string, string>;
}

// Test Steps
export type LocatorStrategy = 'css' | 'xpath' | 'text' | 'role' | 'testId' | 'id' | 'name' | 'placeholder' | 'label';

export interface Assertion {
  type: 'visible' | 'hidden' | 'enabled' | 'disabled' | 'text' | 'value' | 'count' | 'url' | 'title';
  expected: unknown;
  operator?: 'equals' | 'contains' | 'matches' | 'greaterThan' | 'lessThan';
}

export interface TestStep {
  id: UUID;
  order: number;
  action: 'goto' | 'click' | 'fill' | 'select' | 'hover' | 'wait' | 'assert' | 'screenshot' | 'scroll' | 'press' | 'check' | 'uncheck';
  target?: string;
  locator?: string;
  locator_strategy?: LocatorStrategy;
  value?: string;
  options: Record<string, unknown>;
  assertion?: Assertion;
  description?: string;
  continue_on_failure: boolean;
}

export interface CreateTestStepRequest {
  order: number;
  action: TestStep['action'];
  target?: string;
  locator?: string;
  locator_strategy?: LocatorStrategy;
  value?: string;
  options?: Record<string, unknown>;
  assertion?: Assertion;
  description?: string;
  continue_on_failure?: boolean;
}

export interface UpdateTestStepRequest {
  order?: number;
  action?: TestStep['action'];
  target?: string;
  locator?: string;
  locator_strategy?: LocatorStrategy;
  value?: string;
  options?: Record<string, unknown>;
  assertion?: Assertion;
  description?: string;
  continue_on_failure?: boolean;
}

// Test Case
export interface TestCase {
  id: UUID;
  project_id: UUID;
  environment_id?: UUID;
  name: string;
  description?: string;
  steps: TestStep[];
  tags: string[];
  created_at: Timestamp;
  updated_at: Timestamp;
}

export interface CreateTestCaseRequest {
  name: string;
  description?: string;
  steps: CreateTestStepRequest[];
  tags?: string[];
  environment_id?: UUID;
}

export interface UpdateTestCaseRequest {
  name?: string;
  description?: string;
  steps?: CreateTestStepRequest[];
  tags?: string[];
  environment_id?: UUID;
}

export interface GenerateTestCaseRequest {
  intent: string;
  environment_id?: UUID;
  context?: string;
}

// Runs
export type RunStatus = 'pending' | 'running' | 'passed' | 'failed' | 'cancelled' | 'healing';
export type StepStatus = 'pending' | 'running' | 'passed' | 'failed' | 'skipped' | 'healing' | 'healed';

export interface StepExecution {
  id: UUID;
  run_id: UUID;
  step_id: UUID;
  order: number;
  status: StepStatus;
  started_at?: Timestamp;
  finished_at?: Timestamp;
  duration_ms?: number;
  error?: string;
  screenshot_path?: string;
  dom_snapshot_path?: string;
  console_logs: string[];
  network_logs: unknown[];
  trace_path?: string;
  healed_locator?: string;
  healing_candidate_id?: UUID;
}

export interface TestRun {
  id: UUID;
  project_id: UUID;
  test_case_id: UUID;
  environment_id: UUID;
  status: RunStatus;
  started_at?: Timestamp;
  finished_at?: Timestamp;
  duration_ms?: number;
  total_steps: number;
  passed_steps: number;
  failed_steps: number;
  skipped_steps: number;
  triggered_by?: string;
  commit_sha?: string;
  branch?: string;
  created_at: Timestamp;
}

export interface TestRunDetail extends TestRun {
  step_executions: StepExecution[];
}

export interface CreateTestRunRequest {
  test_case_id: UUID;
  environment_id: UUID;
  triggered_by?: string;
  commit_sha?: string;
  branch?: string;
}

// Healing
export type HealingStatus = 'pending' | 'approved' | 'rejected' | 'auto_approved';

export interface HealingCandidate {
  id: UUID;
  run_id: UUID;
  step_execution_id: UUID;
  original_locator: string;
  original_strategy: LocatorStrategy;
  suggested_locator: string;
  suggested_strategy: LocatorStrategy;
  confidence: number;
  reasoning: string;
  status: HealingStatus;
  created_at: Timestamp;
  reviewed_at?: Timestamp;
  reviewed_by?: string;
}

export interface ApproveHealingRequest {
  candidate_id: UUID;
  approved: boolean;
  feedback?: string;
}

// Design Intelligence
export interface VisualBaseline {
  id: UUID;
  project_id: UUID;
  name: string;
  viewport: { width: number; height: number };
  image_path: string;
  created_at: Timestamp;
  updated_at: Timestamp;
}

export interface VisualComparison {
  baseline_id: UUID;
  run_id: UUID;
  step_execution_id: UUID;
  match: boolean;
  difference_percent: number;
  diff_image_path?: string;
  threshold: number;
}

export interface AccessibilityIssue {
  id: UUID;
  run_id: UUID;
  step_execution_id: UUID;
  rule_id: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  description: string;
  help?: string;
  html?: string;
  selector?: string;
}

export interface DesignInsight {
  run_id: UUID;
  visual_comparisons: VisualComparison[];
  accessibility_issues: AccessibilityIssue[];
  performance_metrics?: Record<string, number>;
}

// Memory
export type MemoryType = 'locator' | 'episode' | 'failure_pattern' | 'visual_baseline';

export interface LocatorMemory {
  id: UUID;
  project_id: UUID;
  selector: string;
  strategy: LocatorStrategy;
  page_url: string;
  element_role?: string;
  element_text?: string;
  success_count: number;
  failure_count: number;
  last_used_at: Timestamp;
  created_at: Timestamp;
}

export interface EpisodeMemory {
  id: UUID;
  project_id: UUID;
  intent: string;
  steps: TestStep[];
  outcome: 'success' | 'failure' | 'partial';
  run_id?: UUID;
  created_at: Timestamp;
}

export interface FailurePattern {
  id: UUID;
  project_id: UUID;
  error_pattern: string;
  step_action: string;
  frequency: number;
  suggested_fix?: string;
  last_seen_at: Timestamp;
  created_at: Timestamp;
}

export interface SearchMemoryRequest {
  query: string;
  types?: MemoryType[];
  limit?: number;
}

export interface SearchMemoryResponse {
  locators: LocatorMemory[];
  episodes: EpisodeMemory[];
  failure_patterns: FailurePattern[];
  visual_baselines: VisualBaseline[];
}

// SSE Events
export type SSEEventType = 
  | 'run_started'
  | 'step_started'
  | 'step_completed'
  | 'step_failed'
  | 'healing_candidate'
  | 'healing_approved'
  | 'healing_rejected'
  | 'run_completed'
  | 'run_cancelled'
  | 'log';

export interface SSEEvent {
  type: SSEEventType;
  run_id: UUID;
  timestamp: Timestamp;
  data: unknown;
}

export interface RunStartedData {
  run_id: UUID;
  test_case_id: UUID;
  environment_id: UUID;
}

export interface StepStartedData {
  step_execution_id: UUID;
  step_id: UUID;
  order: number;
  action: string;
  description?: string;
}

export interface StepCompletedData {
  step_execution_id: UUID;
  status: StepStatus;
  duration_ms: number;
  screenshot_path?: string;
}

export interface StepFailedData {
  step_execution_id: UUID;
  error: string;
  healing_candidate?: HealingCandidate;
}

export interface HealingCandidateData {
  candidate: HealingCandidate;
}

export interface RunCompletedData {
  run_id: UUID;
  status: RunStatus;
  duration_ms: number;
  passed_steps: number;
  failed_steps: number;
}

export interface LogData {
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  step_execution_id?: UUID;
}