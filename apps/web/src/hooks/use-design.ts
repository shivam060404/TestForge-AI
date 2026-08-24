import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { DesignInsight, VisualBaseline, VisualComparison, AccessibilityIssue } from '@/types';

const DESIGN_KEY = 'design';

export function useDesignInsights(runId: string) {
  return useQuery({
    queryKey: [DESIGN_KEY, 'insights', runId],
    queryFn: () => api.get<DesignInsight>(`/runs/${runId}/design-insights`),
    select: (response) => response.data,
    enabled: !!runId,
  });
}

export function useVisualBaselines(projectId: string) {
  return useQuery({
    queryKey: [DESIGN_KEY, 'baselines', projectId],
    queryFn: () => api.get<VisualBaseline[]>(`/projects/${projectId}/visual-baselines`),
    select: (response) => response.data,
    enabled: !!projectId,
  });
}

export function useVisualComparison(baselineId: string, runId: string, stepExecutionId: string) {
  return useQuery({
    queryKey: [DESIGN_KEY, 'compare', baselineId, runId, stepExecutionId],
    queryFn: () => api.get<VisualComparison>(`/visual-baselines/${baselineId}/compare?runId=${runId}&stepExecutionId=${stepExecutionId}`),
    select: (response) => response.data,
    enabled: !!baselineId && !!runId && !!stepExecutionId,
  });
}