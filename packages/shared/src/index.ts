import { z } from 'zod';

// ============================================
// Base Types
// ============================================

export const UUIDSchema = z.string().uuid();
export type UUID = z.infer<typeof UUIDSchema>;

export const TimestampSchema = z.string().datetime();
export type Timestamp = z.infer<typeof TimestampSchema>;

export const PaginationSchema = z.object({
  page: z.number().int().positive().default(1),
  pageSize: z.number().int().positive().max(100).default(20),
});
export type Pagination = z.infer<typeof PaginationSchema>;

export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    total: z.number().int().nonnegative(),
    page: z.number().int().positive(),
    pageSize: z.number().int().positive(),
    totalPages: z.number().int().nonnegative(),
  });

// ============================================
// Project
// ============================================

export const ProjectSchema = z.object({
  id: UUIDSchema,
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  createdAt: TimestampSchema,
  updatedAt: TimestampSchema,
});
export type Project = z.infer<typeof ProjectSchema>;

export const CreateProjectSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
});
export type CreateProject = z.infer<typeof CreateProjectSchema>;

export const UpdateProjectSchema = CreateProjectSchema.partial();
export type UpdateProject = z.infer<typeof UpdateProjectSchema>;

// ============================================
// Environment
// ============================================

export const EnvironmentSchema = z.object({
  id: UUIDSchema,
  projectId: UUIDSchema,
  name: z.string().min(1).max(255),
  baseUrl: z.string().url(),
  variables: z.record(z.string()).default({}),
  headers: z.record(z.string()).default({}),
  createdAt: TimestampSchema,
  updatedAt: TimestampSchema,
});
export type Environment = z.infer<typeof EnvironmentSchema>;

export const CreateEnvironmentSchema = z.object({
  name: z.string().min(1).max(255),
  baseUrl: z.string().url(),
  variables: z.record(z.string()).default({}),
  headers: z.record(z.string()).default({}),
});
export type CreateEnvironment = z.infer<typeof CreateEnvironmentSchema>;

export const UpdateEnvironmentSchema = CreateEnvironmentSchema.partial();
export type UpdateEnvironment = z.infer<typeof UpdateEnvironmentSchema>;

// ============================================
// Test Case & Steps
// ============================================

export const LocatorStrategySchema = z.enum([
  'css',
  'xpath',
  'text',
  'role',
  'testId',
  'id',
  'name',
  'placeholder',
  'label',
]);
export type LocatorStrategy = z.infer<typeof LocatorStrategySchema>;

export const TestStepSchema = z.object({
  id: UUIDSchema,
  order: z.number().int().nonnegative(),
  action: z.enum([
    'goto',
    'click',
    'fill',
    'select',
    'hover',
    'wait',
    'assert',
    'screenshot',
    'scroll',
    'press',
    'check',
    'uncheck',
  ]),
  target: z.string().optional(),
  locator: z.string().optional(),
  locatorStrategy: LocatorStrategySchema.optional(),
  value: z.string().optional(),
  options: z.record(z.unknown()).default({}),
  assertion: z.object({
    type: z.enum(['visible', 'hidden', 'enabled', 'disabled', 'text', 'value', 'count', 'url', 'title']),
    expected: z.unknown(),
    operator: z.enum(['equals', 'contains', 'matches', 'greaterThan', 'lessThan']).optional(),
  }).optional(),
  description: z.string().optional(),
  continueOnFailure: z.boolean().default(false),
});
export type TestStep = z.infer<typeof TestStepSchema>;

export const CreateTestStepSchema = TestStepSchema.omit({ id: true });
export type CreateTestStep = z.infer<typeof CreateTestStepSchema>;

export const UpdateTestStepSchema = CreateTestStepSchema.partial();
export type UpdateTestStep = z.infer<typeof UpdateTestStepSchema>;

export const TestCaseSchema = z.object({
  id: UUIDSchema,
  projectId: UUIDSchema,
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  steps: z.array(TestStepSchema),
  tags: z.array(z.string()).default([]),
  createdAt: TimestampSchema,
  updatedAt: TimestampSchema,
});
export type TestCase = z.infer<typeof TestCaseSchema>;

export const CreateTestCaseSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  steps: z.array(CreateTestStepSchema),
  tags: z.array(z.string()).default([]),
});
export type CreateTestCase = z.infer<typeof CreateTestCaseSchema>;

export const UpdateTestCaseSchema = CreateTestCaseSchema.partial();
export type UpdateTestCase = z.infer<typeof UpdateTestCaseSchema>;

export const GenerateTestCaseSchema = z.object({
  intent: z.string().min(10).max(5000),
  environmentId: UUIDSchema.optional(),
  context: z.string().optional(),
});
export type GenerateTestCase = z.infer<typeof GenerateTestCaseSchema>;

// ============================================
// Test Run
// ============================================

export const RunStatusSchema = z.enum([
  'pending',
  'running',
  'passed',
  'failed',
  'cancelled',
  'healing',
]);
export type RunStatus = z.infer<typeof RunStatusSchema>;

export const StepStatusSchema = z.enum([
  'pending',
  'running',
  'passed',
  'failed',
  'skipped',
  'healing',
  'healed',
]);
export type StepStatus = z.infer<typeof StepStatusSchema>;

export const StepExecutionSchema = z.object({
  id: UUIDSchema,
  runId: UUIDSchema,
  stepId: UUIDSchema,
  order: z.number().int().nonnegative(),
  status: StepStatusSchema,
  startedAt: TimestampSchema.optional(),
  finishedAt: TimestampSchema.optional(),
  durationMs: z.number().int().nonnegative().optional(),
  error: z.string().optional(),
  screenshotPath: z.string().optional(),
  domSnapshotPath: z.string().optional(),
  consoleLogs: z.array(z.string()).default([]),
  networkLogs: z.array(z.unknown()).default([]),
  tracePath: z.string().optional(),
  healedLocator: z.string().optional(),
  healingCandidateId: UUIDSchema.optional(),
});
export type StepExecution = z.infer<typeof StepExecutionSchema>;

export const TestRunSchema = z.object({
  id: UUIDSchema,
  projectId: UUIDSchema,
  testCaseId: UUIDSchema,
  environmentId: UUIDSchema,
  status: RunStatusSchema,
  startedAt: TimestampSchema.optional(),
  finishedAt: TimestampSchema.optional(),
  durationMs: z.number().int().nonnegative().optional(),
  totalSteps: z.number().int().nonnegative(),
  passedSteps: z.number().int().nonnegative(),
  failedSteps: z.number().int().nonnegative(),
  skippedSteps: z.number().int().nonnegative(),
  triggeredBy: z.string().optional(),
  commitSha: z.string().optional(),
  branch: z.string().optional(),
});
export type TestRun = z.infer<typeof TestRunSchema>;

export const CreateTestRunSchema = z.object({
  testCaseId: UUIDSchema,
  environmentId: UUIDSchema,
  triggeredBy: z.string().optional(),
  commitSha: z.string().optional(),
  branch: z.string().optional(),
});
export type CreateTestRun = z.infer<typeof CreateTestRunSchema>;

// ============================================
// Healing
// ============================================

export const HealingStatusSchema = z.enum([
  'pending',
  'approved',
  'rejected',
  'auto_approved',
]);
export type HealingStatus = z.infer<typeof HealingStatusSchema>;

export const HealingCandidateSchema = z.object({
  id: UUIDSchema,
  runId: UUIDSchema,
  stepExecutionId: UUIDSchema,
  originalLocator: z.string(),
  originalStrategy: LocatorStrategySchema,
  suggestedLocator: z.string(),
  suggestedStrategy: LocatorStrategySchema,
  confidence: z.number().min(0).max(1),
  reasoning: z.string(),
  status: HealingStatusSchema,
  createdAt: TimestampSchema,
  reviewedAt: TimestampSchema.optional(),
  reviewedBy: z.string().optional(),
});
export type HealingCandidate = z.infer<typeof HealingCandidateSchema>;

export const ApproveHealingSchema = z.object({
  candidateId: UUIDSchema,
  approved: z.boolean(),
  feedback: z.string().optional(),
});
export type ApproveHealing = z.infer<typeof ApproveHealingSchema>;

// ============================================
// Design Intelligence
// ============================================

export const VisualBaselineSchema = z.object({
  id: UUIDSchema,
  projectId: UUIDSchema,
  name: z.string().min(1).max(255),
  viewport: z.object({
    width: z.number().int().positive(),
    height: z.number().int().positive(),
  }),
  imagePath: z.string(),
  createdAt: TimestampSchema,
  updatedAt: TimestampSchema,
});
export type VisualBaseline = z.infer<typeof VisualBaselineSchema>;

export const VisualComparisonResultSchema = z.object({
  baselineId: UUIDSchema,
  runId: UUIDSchema,
  stepExecutionId: UUIDSchema,
  match: z.boolean(),
  differencePercent: z.number().min(0).max(100),
  diffImagePath: z.string().optional(),
  threshold: z.number().min(0).max(100).default(0.1),
});
export type VisualComparisonResult = z.infer<typeof VisualComparisonResultSchema>;

export const AccessibilityIssueSchema = z.object({
  id: UUIDSchema,
  runId: UUIDSchema,
  stepExecutionId: UUIDSchema,
  ruleId: z.string(),
  impact: z.enum(['critical', 'serious', 'moderate', 'minor']),
  description: z.string(),
  help: z.string().optional(),
  html: z.string().optional(),
  selector: z.string().optional(),
});
export type AccessibilityIssue = z.infer<typeof AccessibilityIssueSchema>;

export const DesignInsightSchema = z.object({
  runId: UUIDSchema,
  visualComparisons: z.array(VisualComparisonResultSchema),
  accessibilityIssues: z.array(AccessibilityIssueSchema),
  performanceMetrics: z.record(z.number()).optional(),
});
export type DesignInsight = z.infer<typeof DesignInsightSchema>;

// ============================================
// Memory
// ============================================

export const MemoryTypeSchema = z.enum([
  'locator',
  'episode',
  'failure_pattern',
  'visual_baseline',
]);
export type MemoryType = z.infer<typeof MemoryTypeSchema>;

export const LocatorMemorySchema = z.object({
  id: UUIDSchema,
  projectId: UUIDSchema,
  selector: z.string(),
  strategy: LocatorStrategySchema,
  pageUrl: z.string(),
  elementRole: z.string().optional(),
  elementText: z.string().optional(),
  successCount: z.number().int().nonnegative().default(0),
  failureCount: z.number().int().nonnegative().default(0),
  lastUsedAt: TimestampSchema,
  createdAt: TimestampSchema,
});
export type LocatorMemory = z.infer<typeof LocatorMemorySchema>;

export const EpisodeMemorySchema = z.object({
  id: UUIDSchema,
  projectId: UUIDSchema,
  intent: z.string(),
  steps: z.array(TestStepSchema),
  outcome: z.enum(['success', 'failure', 'partial']),
  runId: UUIDSchema.optional(),
  createdAt: TimestampSchema,
});
export type EpisodeMemory = z.infer<typeof EpisodeMemorySchema>;

export const FailurePatternSchema = z.object({
  id: UUIDSchema,
  projectId: UUIDSchema,
  errorPattern: z.string(),
  stepAction: z.string(),
  frequency: z.number().int().positive(),
  suggestedFix: z.string().optional(),
  lastSeenAt: TimestampSchema,
  createdAt: TimestampSchema,
});
export type FailurePattern = z.infer<typeof FailurePatternSchema>;

export const MemoryEntrySchema = z.union([
  LocatorMemorySchema,
  EpisodeMemorySchema,
  FailurePatternSchema,
  VisualBaselineSchema,
]);
export type MemoryEntry = z.infer<typeof MemoryEntrySchema>;

export const SearchMemorySchema = z.object({
  query: z.string().min(1),
  types: z.array(MemoryTypeSchema).optional(),
  limit: z.number().int().positive().max(100).default(20),
});
export type SearchMemory = z.infer<typeof SearchMemorySchema>;

// ============================================
// SSE Events
// ============================================

export const SSEEventTypeSchema = z.enum([
  'run_started',
  'step_started',
  'step_completed',
  'step_failed',
  'healing_candidate',
  'healing_approved',
  'healing_rejected',
  'run_completed',
  'run_cancelled',
  'log',
]);
export type SSEEventType = z.infer<typeof SSEEventTypeSchema>;

export const SSEEventSchema = z.object({
  type: SSEEventTypeSchema,
  runId: UUIDSchema,
  timestamp: TimestampSchema,
  data: z.unknown(),
});
export type SSEEvent = z.infer<typeof SSEEventSchema>;

export const RunStartedDataSchema = z.object({
  runId: UUIDSchema,
  testCaseId: UUIDSchema,
  environmentId: UUIDSchema,
});
export type RunStartedData = z.infer<typeof RunStartedDataSchema>;

export const StepStartedDataSchema = z.object({
  stepExecutionId: UUIDSchema,
  stepId: UUIDSchema,
  order: z.number().int().nonnegative(),
  action: z.string(),
  description: z.string().optional(),
});
export type StepStartedData = z.infer<typeof StepStartedDataSchema>;

export const StepCompletedDataSchema = z.object({
  stepExecutionId: UUIDSchema,
  status: StepStatusSchema,
  durationMs: z.number().int().nonnegative(),
  screenshotPath: z.string().optional(),
});
export type StepCompletedData = z.infer<typeof StepCompletedDataSchema>;

export const StepFailedDataSchema = z.object({
  stepExecutionId: UUIDSchema,
  error: z.string(),
  healingCandidate: HealingCandidateSchema.optional(),
});
export type StepFailedData = z.infer<typeof StepFailedDataSchema>;

export const HealingCandidateDataSchema = z.object({
  candidate: HealingCandidateSchema,
});
export type HealingCandidateData = z.infer<typeof HealingCandidateDataSchema>;

export const RunCompletedDataSchema = z.object({
  runId: UUIDSchema,
  status: RunStatusSchema,
  durationMs: z.number().int().nonnegative(),
  passedSteps: z.number().int().nonnegative(),
  failedSteps: z.number().int().nonnegative(),
});
export type RunCompletedData = z.infer<typeof RunCompletedDataSchema>;

export const LogDataSchema = z.object({
  level: z.enum(['debug', 'info', 'warn', 'error']),
  message: z.string(),
  stepExecutionId: UUIDSchema.optional(),
});
export type LogData = z.infer<typeof LogDataSchema>;

// ============================================
// API Response Wrappers
// ============================================

export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    data: dataSchema.optional(),
    error: z.object({
      code: z.string(),
      message: z.string(),
      details: z.unknown().optional(),
    }).optional(),
  });

export const ApiErrorSchema = z.object({
  code: z.string(),
  message: z.string(),
  details: z.unknown().optional(),
});
export type ApiError = z.infer<typeof ApiErrorSchema>;