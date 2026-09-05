import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, PaginatedResponse, PaginationParams } from '@/lib/api';
import type { TestCase, CreateTestCaseRequest, UpdateTestCaseRequest, TestStep, GenerateTestCaseRequest } from '@/types';

const TEST_CASES_KEY = 'test-cases';

export function useTestCases(projectId: string, pagination: PaginationParams = {}) {
  return useQuery({
    queryKey: [TEST_CASES_KEY, projectId, pagination],
    queryFn: () => api.get<PaginatedResponse<TestCase>>(`/projects/${projectId}/test-cases`, pagination),
    select: (response) => response.data,
    enabled: !!projectId,
  });
}

export function useTestCase(testCaseId: string) {
  return useQuery({
    queryKey: [TEST_CASES_KEY, testCaseId],
    queryFn: () => api.get<TestCase>(`/test-cases/${testCaseId}`),
    select: (response) => response.data,
    enabled: !!testCaseId,
  });
}

export function useCreateTestCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateTestCaseRequest & { project_id: string }) => {
      const { project_id, ...rest } = data;
      return api.post<TestCase>(`/projects/${project_id}/test-cases`, rest);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [TEST_CASES_KEY, variables.project_id] });
    },
  });
}

export function useUpdateTestCase(testCaseId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateTestCaseRequest) => api.patch<TestCase>(`/test-cases/${testCaseId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TEST_CASES_KEY] });
      queryClient.invalidateQueries({ queryKey: [TEST_CASES_KEY, testCaseId] });
    },
  });
}

export function useDeleteTestCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (testCaseId: string) => api.delete(`/test-cases/${testCaseId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TEST_CASES_KEY] });
    },
  });
}

export function useGenerateTestCase(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GenerateTestCaseRequest) => api.post<TestCase>(`/projects/${projectId}/test-cases/generate`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [TEST_CASES_KEY, projectId] });
    },
  });
}