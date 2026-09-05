import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, PaginatedResponse, PaginationParams } from '@/lib/api';
import type { TestRun, TestRunDetail, CreateTestRunRequest, RunStatus } from '@/types';

const RUNS_KEY = 'runs';

export function useRuns(projectId?: string, params: PaginationParams & { status?: RunStatus } = {}) {
  const { status, ...pagination } = params;
  return useQuery({
    queryKey: [RUNS_KEY, projectId, pagination, status],
    queryFn: () => api.get<PaginatedResponse<TestRun>>(
      projectId ? `/projects/${projectId}/runs` : '/runs',
      { ...pagination, ...(status ? { status } : {}) }
    ),
    select: (response) => response.data,
  });
}

export function useRun(runId: string) {
  return useQuery({
    queryKey: [RUNS_KEY, runId],
    queryFn: () => api.get<TestRunDetail>(`/runs/${runId}`),
    select: (response) => response.data,
    enabled: !!runId,
  });
}

export function useCreateRun() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateTestRunRequest & { project_id?: string }) => {
      const { project_id, ...rest } = data;
      const url = project_id ? `/projects/${project_id}/runs` : '/runs';
      return api.post<TestRun>(url, rest);
    },
    onSuccess: (_, variables) => {
      if (variables.project_id) {
        queryClient.invalidateQueries({ queryKey: [RUNS_KEY, variables.project_id] });
      }
    },
  });
}

export function useCancelRun() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (runId: string) => api.post(`/runs/${runId}/cancel`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [RUNS_KEY] });
    },
  });
}

export function useRetryRun() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (runId: string) => api.post<TestRun>(`/runs/${runId}/retry`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [RUNS_KEY] });
    },
  });
}